import pandas as pd
import numpy as np
from typing import Any, Tuple, Dict, Optional
from datetime import datetime, timedelta
import logging

from app.config import settings
from app.storage.storage_service import get_storage_service
from app.services.data_processor import get_data_processor

logger = logging.getLogger(__name__)


def load_seed() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load seed data from storage (uploaded files or seed directory)

    Priority:
    1. Try loading from storage service (uploaded datasets)
    2. Fall back to seed directory if files don't exist
    """
    storage = get_storage_service()
    processor = get_data_processor()
    data_dir = settings.data_dir

    # Try loading products
    products = pd.DataFrame()
    try:
        if storage.file_exists("products.csv"):
            content = storage.download_file("products.csv")
            products = processor.dataframe_from_csv_bytes(content)
            logger.info(f"Loaded products.csv from storage with {len(products)} rows")
        else:
            # Fall back to seed directory
            products = pd.read_csv(f"{data_dir}/products.csv")
            logger.info(f"Loaded products.csv from seed directory with {len(products)} rows")
    except Exception as e:
        logger.warning(f"Could not load products.csv: {e}")

    # Try loading sales
    sales = pd.DataFrame()
    try:
        if storage.file_exists("sales.csv"):
            content = storage.download_file("sales.csv")
            sales = processor.dataframe_from_csv_bytes(content)
            sales['date'] = pd.to_datetime(sales['date'])
            logger.info(f"Loaded sales.csv from storage with {len(sales)} rows")
        else:
            # Fall back to seed directory
            sales = pd.read_csv(f"{data_dir}/sales.csv", parse_dates=["date"])
            logger.info(f"Loaded sales.csv from seed directory with {len(sales)} rows")
    except Exception as e:
        logger.warning(f"Could not load sales.csv: {e}")

    # Try loading inventory
    inv = pd.DataFrame()
    try:
        if storage.file_exists("inventory.csv"):
            content = storage.download_file("inventory.csv")
            inv = processor.dataframe_from_csv_bytes(content)
            inv['date'] = pd.to_datetime(inv['date'])
            logger.info(f"Loaded inventory.csv from storage with {len(inv)} rows")
        else:
            # Fall back to seed directory
            inv = pd.read_csv(f"{data_dir}/inventory.csv", parse_dates=["date"])
            logger.info(f"Loaded inventory.csv from seed directory with {len(inv)} rows")
    except Exception as e:
        logger.warning(f"Could not load inventory.csv: {e}")

    # Try loading trends (social_trends)
    trends = pd.DataFrame()
    try:
        # Note: social_trends is not uploadable via UI yet, only from seed
        trends = pd.read_csv(f"{data_dir}/social_trends.csv", parse_dates=["timestamp"])
        logger.info(f"Loaded social_trends.csv from seed directory with {len(trends)} rows")
    except Exception as e:
        logger.warning(f"Could not load social_trends.csv: {e}")

    return products, sales, inv, trends


def aggregate_by_sku(sales: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sales by date, store, SKU"""
    if sales.empty or products.empty:
        return pd.DataFrame()

    # Join sales with product info
    sales_joined = sales.merge(products, on='sku', how='left')

    # Aggregate by date, store_id, channel, sku
    agg_sku = sales_joined.groupby(
        ['date', 'store_id', 'channel', 'sku'],
        as_index=False
    ).agg({
        'units_sold': 'sum',
        'promo_flag': 'max',  # 1 if any promo that day
        'price': 'mean',
        'style_code': 'first',
        'style_desc': 'first',
        'color_name': 'first',
        'size': 'first',
        'category': 'first'
    })

    return agg_sku


def aggregate_by_attribute(sales: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sales by date, store, and attribute triplet (size, color, style)"""
    if sales.empty or products.empty:
        return pd.DataFrame()

    # Join sales with product info
    sales_joined = sales.merge(products, on='sku', how='left')

    # Aggregate by attribute triplet
    agg_attr = sales_joined.groupby(
        ['date', 'store_id', 'channel', 'color_name', 'size', 'style_desc'],
        as_index=False
    ).agg({
        'units_sold': 'sum',
        'promo_flag': 'max',
        'price': 'mean',
        'category': 'first',
        'style_code': 'first'
    })

    return agg_attr


def add_moving_averages(df: pd.DataFrame, windows: list = [7, 28]) -> pd.DataFrame:
    """Add moving average features for sales"""
    if df.empty or 'units_sold' not in df.columns:
        return df

    # Sort by date for proper rolling calculations
    df = df.sort_values('date')

    # Group by store and SKU/attributes
    group_cols = ['store_id']
    if 'sku' in df.columns:
        group_cols.append('sku')
    elif 'color_name' in df.columns:
        group_cols.extend(['color_name', 'size', 'style_desc'])

    for window in windows:
        col_name = f'ma_{window}d'
        df[col_name] = df.groupby(group_cols)['units_sold'].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean()
        )

    return df


def add_promo_rate(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """Add promo rate feature (% of days with promo in last N days)"""
    if df.empty or 'promo_flag' not in df.columns:
        return df

    df = df.sort_values('date')

    group_cols = ['store_id']
    if 'sku' in df.columns:
        group_cols.append('sku')
    elif 'color_name' in df.columns:
        group_cols.extend(['color_name', 'size', 'style_desc'])

    df['promo_rate_7d'] = df.groupby(group_cols)['promo_flag'].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )

    return df


def add_price_index(df: pd.DataFrame) -> pd.DataFrame:
    """Add price index (current price / average price)"""
    if df.empty or 'price' not in df.columns:
        return df

    group_cols = ['store_id']
    if 'sku' in df.columns:
        group_cols.append('sku')
    elif 'color_name' in df.columns:
        group_cols.extend(['color_name', 'size', 'style_desc'])

    # Calculate average price per group
    avg_price = df.groupby(group_cols)['price'].transform('mean')
    df['price_index'] = df['price'] / (avg_price + 1e-6)  # Avoid division by zero

    return df


def add_seasonality_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add seasonality features (sin/cos of day of year)"""
    if df.empty or 'date' not in df.columns:
        return df

    # Extract day of year
    df['day_of_year'] = pd.to_datetime(df['date']).dt.dayofyear

    # Convert to cyclical features
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365.25)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365.25)

    # Add day of week
    df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

    return df


def add_stock_coverage(df: pd.DataFrame, inv: pd.DataFrame) -> pd.DataFrame:
    """Add stock coverage feature (on_hand / 7-day avg sales)"""
    if df.empty or inv.empty:
        return df

    # Merge inventory data
    merge_cols = ['date', 'store_id']
    if 'sku' in df.columns and 'sku' in inv.columns:
        merge_cols.append('sku')
        df = df.merge(
            inv[['date', 'store_id', 'sku', 'on_hand', 'on_order', 'lead_time_days']],
            on=merge_cols,
            how='left'
        )

        # Calculate stock coverage
        df['stock_coverage'] = df['on_hand'] / (df.get('ma_7d', 1) + 1e-6)
        df['incoming_coverage'] = df['on_order'] / (df.get('ma_7d', 1) + 1e-6)

    return df


def add_trend_signals(df: pd.DataFrame, trends: pd.DataFrame) -> pd.DataFrame:
    """Add trend signals from social data"""
    if df.empty or trends.empty:
        return df

    # Extract date from timestamp
    if 'timestamp' in trends.columns:
        trends['date'] = pd.to_datetime(trends['timestamp']).dt.date
        trends['date'] = pd.to_datetime(trends['date'])

    # Aggregate trend scores by date and color
    if 'color_name' in df.columns and 'color_name' in trends.columns:
        trend_agg = trends.groupby(['date', 'color_name'], as_index=False).agg({
            'trend_score': 'mean'
        })

        df = df.merge(
            trend_agg,
            left_on=['date', 'color_name'],
            right_on=['date', 'color_name'],
            how='left'
        )

        # Fill missing trend scores with neutral value
        df['trend_score'] = df['trend_score'].fillna(0.5)

    return df


def load_features(req: Any) -> Dict[str, pd.DataFrame]:
    """Load and engineer features for forecasting

    Returns a dictionary with:
    - sku_features: Features aggregated by SKU
    - attribute_features: Features aggregated by attribute triplet
    - metadata: Product and trend metadata
    """
    products, sales, inv, trends = load_seed()

    if sales.empty:
        return {
            "sku_features": pd.DataFrame(),
            "attribute_features": pd.DataFrame(),
            "metadata": {"products": products, "trends": trends}
        }

    # Aggregate by SKU
    sku_agg = aggregate_by_sku(sales, products)
    if not sku_agg.empty:
        sku_agg = add_moving_averages(sku_agg, windows=[7, 28])
        sku_agg = add_promo_rate(sku_agg, window=7)
        sku_agg = add_price_index(sku_agg)
        sku_agg = add_seasonality_features(sku_agg)
        sku_agg = add_stock_coverage(sku_agg, inv)

    # Aggregate by attribute triplet
    attr_agg = aggregate_by_attribute(sales, products)
    if not attr_agg.empty:
        attr_agg = add_moving_averages(attr_agg, windows=[7, 28])
        attr_agg = add_promo_rate(attr_agg, window=7)
        attr_agg = add_price_index(attr_agg)
        attr_agg = add_seasonality_features(attr_agg)
        attr_agg = add_trend_signals(attr_agg, trends)

    return {
        "sku_features": sku_agg,
        "attribute_features": attr_agg,
        "metadata": {
            "products": products,
            "trends": trends,
            "inventory": inv
        }
    }


def get_feature_matrix(
    df: pd.DataFrame,
    feature_cols: Optional[list] = None
) -> Tuple[np.ndarray, list]:
    """Extract feature matrix from engineered dataframe

    Args:
        df: DataFrame with engineered features
        feature_cols: List of columns to use as features. If None, auto-select numeric cols

    Returns:
        Feature matrix (numpy array) and list of feature names
    """
    if df.empty:
        return np.array([]), []

    if feature_cols is None:
        # Auto-select numeric feature columns
        feature_cols = [
            'units_sold', 'promo_flag', 'price',
            'ma_7d', 'ma_28d', 'promo_rate_7d', 'price_index',
            'day_sin', 'day_cos', 'dow_sin', 'dow_cos'
        ]

        # Add optional features if they exist
        optional_cols = ['stock_coverage', 'incoming_coverage', 'trend_score']
        feature_cols.extend([col for col in optional_cols if col in df.columns])

        # Filter to only columns that exist
        feature_cols = [col for col in feature_cols if col in df.columns]

    # Extract feature matrix
    X = df[feature_cols].fillna(0).values

    return X, feature_cols
