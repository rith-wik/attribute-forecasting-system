from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
import glob
from app.services.data_pipeline import load_features, get_feature_matrix
from app.services.explain import explain_contribs
from app.services.baseline_model import HybridForecaster
from app.config import settings

@dataclass
class ForecastService:
    model_path: str = None
    trained_model: Optional[HybridForecaster] = None

    def __post_init__(self):
        if self.model_path is None:
            self.model_path = settings.model_path

        # Try to load the latest trained model
        self._load_latest_model()

    def _load_latest_model(self):
        """Load the most recently trained model"""
        model_dir = "./artifacts"
        if not os.path.exists(model_dir):
            return

        # Find all model files
        model_files = glob.glob(f"{model_dir}/afs-*.pkl")
        if not model_files:
            return

        # Get the most recent one
        latest_model = max(model_files, key=os.path.getmtime)

        try:
            self.trained_model = HybridForecaster.load(latest_model)
            self.model_path = latest_model
        except Exception as e:
            print(f"Failed to load model from {latest_model}: {e}")
            self.trained_model = None

    def predict(self, req) -> Dict[str, Any]:
        """Generate forecasts for the request"""
        # Load and engineer features
        feature_data = load_features(req)

        # Select appropriate features based on level
        if req.level == "attribute":
            df = feature_data.get("attribute_features", pd.DataFrame())
        else:
            df = feature_data.get("sku_features", pd.DataFrame())

        # Generate forecasts
        forecasts = self._baseline_forecast(df, req, feature_data)
        resp = self._format_response(forecasts, req, feature_data)
        return resp

    def _baseline_forecast(self, df: pd.DataFrame, req, feature_data: Dict) -> pd.DataFrame:
        """Generate forecast using trained model or fallback to MA

        Priority:
        1. Use trained HybridForecaster if available
        2. Fallback to 7-day MA baseline
        3. Apply what-if adjustments
        """
        if df.empty:
            return pd.DataFrame()

        # Filter to requested stores/SKUs if specified
        if req.store_ids:
            df = df[df['store_id'].isin(req.store_ids)]

        if req.skus and 'sku' in df.columns:
            df = df[df['sku'].isin(req.skus)]

        # Try to use trained model
        if self.trained_model is not None:
            try:
                predictions = self.trained_model.predict(df)
                df['forecast_base'] = predictions
            except Exception as e:
                print(f"Model prediction failed: {e}, falling back to MA")
                # Fallback to MA
                if 'ma_7d' in df.columns:
                    df['forecast_base'] = df['ma_7d']
                else:
                    df['forecast_base'] = df.get('units_sold', 1.0)
        else:
            # No trained model, use MA
            if 'ma_7d' in df.columns:
                df['forecast_base'] = df['ma_7d']
            else:
                df['forecast_base'] = df.get('units_sold', 1.0)

        # Apply what-if adjustments
        if req.what_if:
            df = self._apply_what_if(df, req.what_if)

        return df

    def _apply_what_if(self, df: pd.DataFrame, what_if) -> pd.DataFrame:
        """Apply what-if scenario adjustments with realistic elasticities

        Uses econometric-informed elasticities:
        - Price elasticity: -1.5 (15% demand drop for 10% price increase)
        - Promo lift: +25% baseline
        - Trend boost: Direct multiplier on demand
        """
        df = df.copy()

        # Price delta adjustment with category-dependent elasticity
        if what_if.price_delta is not None and 'price' in df.columns:
            # Calculate price change percentage
            current_price = df['price'].mean()
            price_change_pct = what_if.price_delta / current_price if current_price > 0 else 0

            # Use realistic price elasticity (typically -1.0 to -2.0 for retail)
            # More elastic for discretionary items
            price_elasticity = -1.5

            # Apply elasticity formula: %ΔQ = elasticity * %ΔP
            demand_multiplier = 1 + (price_elasticity * price_change_pct)
            demand_multiplier = max(0.3, min(2.0, demand_multiplier))  # Clamp to reasonable range

            df['forecast_base'] = df['forecast_base'] * demand_multiplier
            df['what_if_price_impact'] = demand_multiplier - 1.0  # Track for explainability

        # Promo adjustment with more realistic lift
        if what_if.promo_flag == 1:
            # Promo typically gives 20-30% lift depending on category
            promo_lift = 1.25  # 25% lift

            # If there's already a promo in historical data, increment is smaller
            if 'promo_rate_7d' in df.columns:
                historical_promo = df['promo_rate_7d'].mean()
                # Reduce lift if already running promos frequently
                promo_lift = 1.25 * (1 - 0.5 * historical_promo)

            df['forecast_base'] = df['forecast_base'] * promo_lift
            df['what_if_promo_impact'] = promo_lift - 1.0

        # Trend boost by color with saturation effects
        if what_if.trend_boost and 'color_name' in df.columns:
            for color, boost in what_if.trend_boost.items():
                mask = df['color_name'] == color

                # Apply boost with diminishing returns for large values
                # Use sigmoid-like function to prevent unrealistic spikes
                effective_boost = boost / (1 + abs(boost) * 0.5)

                df.loc[mask, 'forecast_base'] = df.loc[mask, 'forecast_base'] * (1 + effective_boost)
                df.loc[mask, 'what_if_trend_impact'] = effective_boost

        return df

    def _format_response(self, forecasts: pd.DataFrame, req, feature_data: Dict) -> Dict[str, Any]:
        """Convert forecast DataFrame to API schema"""
        generated_at = datetime.utcnow().isoformat() + "Z"

        if forecasts.empty:
            # Return mock data if no features available
            return self._mock_response(req, generated_at)

        results = []
        products = feature_data.get("metadata", {}).get("products", pd.DataFrame())

        # Group by store and SKU/attribute
        if req.level == "attribute":
            group_cols = ['store_id', 'color_name', 'size', 'style_desc']
        else:
            group_cols = ['store_id', 'sku'] if 'sku' in forecasts.columns else ['store_id']

        for name, group in forecasts.groupby(group_cols):
            # Get latest forecast values
            latest = group.sort_values('date').iloc[-1] if 'date' in group.columns else group.iloc[0]

            # Generate daily forecasts with realistic confidence intervals
            daily_forecasts = []
            start_date = datetime.now().date()
            base_forecast = latest.get('forecast_base', 1.0)

            # Calculate uncertainty metrics
            ma_7d = latest.get('ma_7d', base_forecast)
            ma_28d = latest.get('ma_28d', base_forecast)

            # Estimate volatility from MA ratio (higher ratio = more volatile)
            volatility_factor = abs(ma_7d - ma_28d) / (ma_28d + 1e-6) if ma_28d > 0 else 0.2
            volatility_factor = max(0.1, min(0.5, volatility_factor))  # Clamp between 10-50%

            for i in range(req.horizon_days):
                forecast_date = start_date + timedelta(days=i+1)

                # Add seasonality pattern (day of week effect)
                dow = forecast_date.weekday()
                dow_multiplier = 1.0 + 0.1 * np.sin(2 * np.pi * dow / 7)  # ±10% variation

                # Apply slight trend if present in recent data
                trend_factor = (ma_7d / (ma_28d + 1e-6)) if ma_28d > 0 else 1.0
                trend_factor = max(0.8, min(1.2, trend_factor))  # Limit trend to ±20%

                # Calculate daily forecast
                day_forecast = base_forecast * dow_multiplier * (trend_factor ** (i / 30))

                # Confidence intervals widen with horizon
                # Start at ±20% for day 1, grow to ±40% by day 30
                ci_width_factor = 0.2 + (0.2 * i / 30)  # Grows from 0.2 to 0.4
                ci_width = ci_width_factor * (1 + volatility_factor)

                lo = day_forecast * (1 - ci_width)
                hi = day_forecast * (1 + ci_width)

                daily_forecasts.append({
                    "date": forecast_date.isoformat(),
                    "forecast_units": round(max(0, day_forecast), 2),
                    "lo": round(max(0, lo), 2),
                    "hi": round(hi, 2)
                })

            # Build result object
            if req.level == "attribute":
                result = {
                    "store_id": latest['store_id'],
                    "sku": f"{latest.get('style_code', 'UNK')}-{latest.get('color_name', 'UNK')[:3]}-{latest.get('size', 'M')}",
                    "attributes": {
                        "color": latest.get('color_name', 'Unknown'),
                        "size": latest.get('size', 'M'),
                        "style": latest.get('style_desc', 'Unknown')
                    },
                    "daily": daily_forecasts,
                    "explain": explain_contribs(latest)
                }
            else:
                # SKU level
                sku = latest.get('sku', 'A1001')
                prod_info = products[products['sku'] == sku].iloc[0] if not products.empty and sku in products['sku'].values else {}
                result = {
                    "store_id": latest['store_id'],
                    "sku": sku,
                    "attributes": {
                        "color": prod_info.get('color_name', latest.get('color_name', 'Black')),
                        "size": prod_info.get('size', latest.get('size', 'M')),
                        "style": prod_info.get('style_desc', latest.get('style_desc', 'Unknown'))
                    },
                    "daily": daily_forecasts,
                    "explain": explain_contribs(latest)
                }

            results.append(result)

        return {
            "generated_at": generated_at,
            "horizon_days": req.horizon_days,
            "results": results
        }

    def _mock_response(self, req, generated_at: str) -> Dict[str, Any]:
        """Generate mock response when no data available"""
        results = []
        skus = req.skus or ["A1001"]
        store_ids = req.store_ids or ["DXB01"]

        for store_id in store_ids:
            for sku in skus:
                daily_forecasts = []
                start_date = datetime.now().date()

                for i in range(min(req.horizon_days, 7)):
                    forecast_date = start_date + timedelta(days=i+1)
                    daily_forecasts.append({
                        "date": forecast_date.isoformat(),
                        "forecast_units": 0.9 + i * 0.1,
                        "lo": 0.6 + i * 0.1,
                        "hi": 1.2 + i * 0.1
                    })

                results.append({
                    "store_id": store_id,
                    "sku": sku,
                    "attributes": {
                        "color": "Black",
                        "size": "M",
                        "style": "Slim Tee"
                    },
                    "daily": daily_forecasts,
                    "explain": explain_contribs()
                })

        return {
            "generated_at": generated_at,
            "horizon_days": req.horizon_days,
            "results": results
        }
