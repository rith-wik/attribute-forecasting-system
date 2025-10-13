import pytest
import pandas as pd
import numpy as np
from app.services.data_pipeline import (
    load_seed,
    load_features,
    aggregate_by_sku,
    aggregate_by_attribute,
    add_moving_averages,
    add_promo_rate,
    add_price_index,
    add_seasonality_features,
    add_stock_coverage,
    add_trend_signals,
    get_feature_matrix
)

def test_load_seed():
    """Test that seed data loads correctly"""
    products, sales, inv, trends = load_seed()
    # Even if files don't exist, should return DataFrames
    assert products is not None
    assert sales is not None
    assert inv is not None
    assert trends is not None
    assert isinstance(products, pd.DataFrame)
    assert isinstance(sales, pd.DataFrame)

def test_load_features():
    """Test main feature loading function"""
    class MockRequest:
        horizon_days = 7
        store_ids = ["DXB01"]
        skus = ["A1001"]
        level = "attribute"
        what_if = None

    result = load_features(MockRequest())
    assert result is not None
    assert "sku_features" in result
    assert "attribute_features" in result
    assert "metadata" in result

def test_aggregate_by_sku():
    """Test SKU-level aggregation"""
    # Create sample data
    sales = pd.DataFrame({
        'date': pd.to_datetime(['2025-07-01', '2025-07-01', '2025-07-02']),
        'store_id': ['DXB01', 'DXB01', 'DXB01'],
        'channel': ['store', 'store', 'store'],
        'sku': ['A1001', 'A1001', 'A1002'],
        'units_sold': [5, 3, 4],
        'promo_flag': [0, 1, 0],
        'price': [19.99, 17.99, 19.99]
    })

    products = pd.DataFrame({
        'sku': ['A1001', 'A1002'],
        'style_code': ['ST-001', 'ST-001'],
        'style_desc': ['Slim Tee', 'Slim Tee'],
        'color_name': ['Black', 'Black'],
        'size': ['M', 'L'],
        'category': ['Tops', 'Tops']
    })

    result = aggregate_by_sku(sales, products)
    assert not result.empty
    assert 'units_sold' in result.columns
    assert 'color_name' in result.columns
    # Check aggregation: should have 2 rows (2 date-sku combinations)
    assert len(result) == 2

def test_aggregate_by_attribute():
    """Test attribute-level aggregation"""
    sales = pd.DataFrame({
        'date': pd.to_datetime(['2025-07-01', '2025-07-01']),
        'store_id': ['DXB01', 'DXB01'],
        'channel': ['store', 'store'],
        'sku': ['A1001', 'A1002'],
        'units_sold': [5, 3],
        'promo_flag': [0, 0],
        'price': [19.99, 19.99]
    })

    products = pd.DataFrame({
        'sku': ['A1001', 'A1002'],
        'style_desc': ['Slim Tee', 'Slim Tee'],
        'color_name': ['Black', 'Black'],
        'size': ['M', 'L'],
        'category': ['Tops', 'Tops'],
        'style_code': ['ST-001', 'ST-001']
    })

    result = aggregate_by_attribute(sales, products)
    assert not result.empty
    assert 'color_name' in result.columns
    assert 'size' in result.columns
    assert 'style_desc' in result.columns

def test_add_moving_averages():
    """Test moving average feature engineering"""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2025-07-01', '2025-07-02', '2025-07-03', '2025-07-04']),
        'store_id': ['DXB01', 'DXB01', 'DXB01', 'DXB01'],
        'sku': ['A1001', 'A1001', 'A1001', 'A1001'],
        'units_sold': [5, 6, 7, 8]
    })

    result = add_moving_averages(df, windows=[3])
    assert 'ma_3d' in result.columns
    # Check that MA is calculated correctly
    assert result.iloc[2]['ma_3d'] == pytest.approx((5 + 6 + 7) / 3, rel=0.01)

def test_add_seasonality_features():
    """Test seasonality feature engineering"""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2025-07-01', '2025-07-02'])
    })

    result = add_seasonality_features(df)
    assert 'day_sin' in result.columns
    assert 'day_cos' in result.columns
    assert 'dow_sin' in result.columns
    assert 'dow_cos' in result.columns
    # Check that values are in valid range [-1, 1]
    assert result['day_sin'].abs().max() <= 1
    assert result['day_cos'].abs().max() <= 1

def test_add_price_index():
    """Test price index feature"""
    df = pd.DataFrame({
        'store_id': ['DXB01', 'DXB01', 'DXB01'],
        'sku': ['A1001', 'A1001', 'A1001'],
        'price': [20.0, 18.0, 22.0]
    })

    result = add_price_index(df)
    assert 'price_index' in result.columns
    # Average price is 20, so indices should be 1.0, 0.9, 1.1
    assert result['price_index'].iloc[0] == pytest.approx(1.0, rel=0.01)
    assert result['price_index'].iloc[1] == pytest.approx(0.9, rel=0.01)
    assert result['price_index'].iloc[2] == pytest.approx(1.1, rel=0.01)

def test_add_promo_rate():
    """Test promo rate feature"""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2025-07-01', '2025-07-02', '2025-07-03']),
        'store_id': ['DXB01', 'DXB01', 'DXB01'],
        'sku': ['A1001', 'A1001', 'A1001'],
        'promo_flag': [0, 1, 1]
    })

    result = add_promo_rate(df, window=3)
    assert 'promo_rate_7d' in result.columns
    # Last row should have promo_rate = 2/3
    assert result.iloc[-1]['promo_rate_7d'] == pytest.approx(2/3, rel=0.01)

def test_get_feature_matrix():
    """Test feature matrix extraction"""
    df = pd.DataFrame({
        'units_sold': [5, 6, 7],
        'promo_flag': [0, 1, 0],
        'price': [19.99, 17.99, 19.99],
        'ma_7d': [5.5, 6.0, 6.5],
        'ma_28d': [5.2, 5.8, 6.2]
    })

    X, feature_cols = get_feature_matrix(df)
    assert X.shape[0] == 3  # 3 rows
    assert X.shape[1] > 0   # At least some features
    assert len(feature_cols) == X.shape[1]
    assert 'units_sold' in feature_cols

def test_feature_pipeline_integration():
    """Integration test: verify all features are engineered correctly"""
    products, sales, inv, trends = load_seed()

    if not sales.empty and not products.empty:
        # Test SKU aggregation
        sku_agg = aggregate_by_sku(sales, products)
        assert not sku_agg.empty

        # Test feature engineering pipeline
        sku_agg = add_moving_averages(sku_agg, windows=[7, 28])
        assert 'ma_7d' in sku_agg.columns
        assert 'ma_28d' in sku_agg.columns

        sku_agg = add_promo_rate(sku_agg)
        assert 'promo_rate_7d' in sku_agg.columns

        sku_agg = add_price_index(sku_agg)
        assert 'price_index' in sku_agg.columns

        sku_agg = add_seasonality_features(sku_agg)
        assert 'day_sin' in sku_agg.columns
        assert 'day_cos' in sku_agg.columns

        # Test attribute aggregation
        attr_agg = aggregate_by_attribute(sales, products)
        assert not attr_agg.empty
        assert 'color_name' in attr_agg.columns
        assert 'size' in attr_agg.columns
        assert 'style_desc' in attr_agg.columns
