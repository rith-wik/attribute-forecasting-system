from typing import Dict, Any, Optional
import pandas as pd

def explain_contribs(data: Optional[Any] = None) -> Dict[str, float]:
    """Return per-feature contributions for explainability

    Args:
        data: Optional row data (Series or dict) with feature values

    Returns:
        Dictionary of feature contributions
    """
    if data is None or (isinstance(data, pd.Series) and data.empty):
        # Return default mock attributions
        return {
            "price": -0.12,
            "trend_Black": 0.25,
            "seasonality": 0.18
        }

    # Convert to dict if Series
    if isinstance(data, pd.Series):
        data = data.to_dict()

    contribs = {}

    # Price contribution (negative if price is high)
    if 'price_index' in data:
        price_idx = data['price_index']
        contribs['price'] = (1.0 - price_idx) * 0.15

    # Promo contribution
    if 'promo_flag' in data or 'promo_rate_7d' in data:
        promo_rate = data.get('promo_rate_7d', data.get('promo_flag', 0))
        contribs['promo'] = promo_rate * 0.20

    # Trend contribution (from social signals)
    if 'trend_score' in data:
        trend_score = data['trend_score']
        contribs[f"trend_{data.get('color_name', 'color')}"] = (trend_score - 0.5) * 0.30

    # Seasonality contribution
    if 'day_sin' in data and 'day_cos' in data:
        # Combine sin/cos into magnitude
        import math
        magnitude = math.sqrt(data['day_sin']**2 + data['day_cos']**2)
        contribs['seasonality'] = magnitude * 0.15

    # Stock availability contribution
    if 'stock_coverage' in data:
        stock_cov = data['stock_coverage']
        if stock_cov < 1.0:
            contribs['stock_constraint'] = -0.20  # Negative if low stock
        elif stock_cov > 5.0:
            contribs['overstock'] = -0.05  # Slight negative if overstocked

    # MA trend (recent momentum)
    if 'ma_7d' in data and 'ma_28d' in data:
        ma_ratio = data['ma_7d'] / (data['ma_28d'] + 1e-6)
        contribs['momentum'] = (ma_ratio - 1.0) * 0.25

    # If no features found, return defaults
    if not contribs:
        return {
            "price": -0.12,
            "trend": 0.25,
            "seasonality": 0.18
        }

    return contribs
