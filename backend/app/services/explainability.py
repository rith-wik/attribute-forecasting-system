"""Advanced explainability module with permutation importance"""
import numpy as np
import pandas as pd
from typing import Dict, Optional, Any, Callable
from app.services.baseline_model import HybridForecaster


def permutation_importance(
    model: HybridForecaster,
    X: pd.DataFrame,
    y: pd.Series,
    n_repeats: int = 10,
    random_state: int = 42
) -> Dict[str, float]:
    """Calculate permutation importance for model features

    Similar to SHAP but faster and model-agnostic.
    Measures how much each feature contributes to predictions.

    Args:
        model: Trained forecasting model
        X: Feature dataframe
        y: True values
        n_repeats: Number of permutation repetitions
        random_state: Random seed for reproducibility

    Returns:
        Dictionary mapping feature names to importance scores
    """
    np.random.seed(random_state)

    # Get baseline predictions and error
    baseline_preds = model.predict(X)
    baseline_error = np.mean(np.abs(y - baseline_preds))

    importance_scores = {}

    # Test each feature by permuting it
    for feature in X.columns:
        importances = []

        for _ in range(n_repeats):
            # Create copy of X
            X_permuted = X.copy()

            # Permute this feature
            X_permuted[feature] = np.random.permutation(X_permuted[feature].values)

            # Get predictions with permuted feature
            permuted_preds = model.predict(X_permuted)
            permuted_error = np.mean(np.abs(y - permuted_preds))

            # Importance is increase in error
            importance = permuted_error - baseline_error
            importances.append(importance)

        # Average over repeats
        importance_scores[feature] = np.mean(importances)

    # Normalize to sum to 1
    total = sum(abs(v) for v in importance_scores.values())
    if total > 0:
        importance_scores = {k: v / total for k, v in importance_scores.items()}

    return importance_scores


def feature_attribution(
    row_data: pd.Series,
    model: Optional[HybridForecaster] = None,
    feature_importance: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """Calculate feature attribution for a single prediction

    Combines model-based importance with local feature values
    to explain a specific prediction.

    Args:
        row_data: Single row of features
        model: Trained model (optional, for feature importance)
        feature_importance: Pre-computed feature importance (optional)

    Returns:
        Dictionary of feature contributions
    """
    # If we have a model, get feature importance
    if model is not None and feature_importance is None:
        feature_importance = model.get_feature_importance()

    # If no importance available, use heuristics
    if feature_importance is None or len(feature_importance) == 0:
        return _heuristic_attribution(row_data)

    # Combine feature importance with local values
    attributions = {}

    for feature, importance in feature_importance.items():
        if feature in row_data:
            value = row_data[feature]

            # Normalize value to [-1, 1] range
            if feature.endswith('_sin') or feature.endswith('_cos'):
                # Already in [-1, 1]
                normalized_value = value
            elif feature == 'price_index':
                # Center around 1.0
                normalized_value = value - 1.0
            elif feature == 'promo_flag' or feature.startswith('promo'):
                # Binary or rate
                normalized_value = value
            else:
                # For other features, assume positive values
                # Normalize by clipping to reasonable range
                normalized_value = np.clip(value, 0, 10) / 10

            # Attribution is importance * normalized value
            attribution = importance * normalized_value
            attributions[feature] = attribution

    # Add what-if impacts if present
    if 'what_if_price_impact' in row_data and not pd.isna(row_data['what_if_price_impact']):
        attributions['what_if_price'] = row_data['what_if_price_impact']

    if 'what_if_promo_impact' in row_data and not pd.isna(row_data['what_if_promo_impact']):
        attributions['what_if_promo'] = row_data['what_if_promo_impact']

    if 'what_if_trend_impact' in row_data and not pd.isna(row_data['what_if_trend_impact']):
        attributions['what_if_trend'] = row_data['what_if_trend_impact']

    return attributions


def _heuristic_attribution(row_data: pd.Series) -> Dict[str, float]:
    """Fallback heuristic attribution when no model available"""
    attributions = {}

    # Price contribution
    if 'price_index' in row_data:
        price_idx = row_data['price_index']
        attributions['price'] = (1.0 - price_idx) * 0.15

    # Promo contribution
    if 'promo_flag' in row_data or 'promo_rate_7d' in row_data:
        promo_rate = row_data.get('promo_rate_7d', row_data.get('promo_flag', 0))
        attributions['promo'] = promo_rate * 0.20

    # Trend contribution
    if 'trend_score' in row_data:
        trend_score = row_data['trend_score']
        attributions[f"trend_{row_data.get('color_name', 'color')}"] = (trend_score - 0.5) * 0.30

    # Seasonality
    if 'day_sin' in row_data and 'day_cos' in row_data:
        magnitude = np.sqrt(row_data['day_sin']**2 + row_data['day_cos']**2)
        attributions['seasonality'] = magnitude * 0.15

    # Momentum
    if 'ma_7d' in row_data and 'ma_28d' in row_data:
        ma_ratio = row_data['ma_7d'] / (row_data['ma_28d'] + 1e-6)
        attributions['momentum'] = (ma_ratio - 1.0) * 0.25

    # Stock
    if 'stock_coverage' in row_data:
        stock_cov = row_data['stock_coverage']
        if stock_cov < 1.0:
            attributions['stock_constraint'] = -0.20
        elif stock_cov > 5.0:
            attributions['overstock'] = -0.05

    return attributions


def explain_forecast_change(
    baseline_forecast: float,
    new_forecast: float,
    what_if_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Explain why forecast changed from baseline

    Args:
        baseline_forecast: Original forecast
        new_forecast: New forecast after adjustments
        what_if_params: What-if parameters that were applied

    Returns:
        Dictionary with explanation
    """
    change = new_forecast - baseline_forecast
    change_pct = (change / baseline_forecast * 100) if baseline_forecast > 0 else 0

    explanation = {
        'baseline_forecast': round(baseline_forecast, 2),
        'new_forecast': round(new_forecast, 2),
        'absolute_change': round(change, 2),
        'percent_change': round(change_pct, 1),
        'drivers': []
    }

    if what_if_params:
        # Explain each what-if parameter's contribution
        if 'price_delta' in what_if_params and what_if_params['price_delta'] is not None:
            price_delta = what_if_params['price_delta']
            direction = 'decrease' if price_delta < 0 else 'increase'
            explanation['drivers'].append({
                'factor': 'price',
                'description': f"${abs(price_delta):.2f} price {direction}",
                'impact': 'positive' if price_delta < 0 else 'negative'
            })

        if 'promo_flag' in what_if_params and what_if_params['promo_flag'] == 1:
            explanation['drivers'].append({
                'factor': 'promotion',
                'description': 'Promotional campaign active',
                'impact': 'positive'
            })

        if 'trend_boost' in what_if_params and what_if_params['trend_boost']:
            for color, boost in what_if_params['trend_boost'].items():
                explanation['drivers'].append({
                    'factor': 'trend',
                    'description': f"{color} trending {'+' if boost > 0 else ''}{boost*100:.0f}%",
                    'impact': 'positive' if boost > 0 else 'negative'
                })

    return explanation


def generate_sensitivity_analysis(
    model: HybridForecaster,
    base_features: pd.DataFrame,
    feature_ranges: Optional[Dict[str, tuple]] = None
) -> Dict[str, Any]:
    """Generate sensitivity analysis showing forecast response to feature changes

    Args:
        model: Trained model
        base_features: Baseline feature values
        feature_ranges: Dict mapping features to (min, max) tuples to test

    Returns:
        Sensitivity results for each feature
    """
    if feature_ranges is None:
        # Default ranges for common features
        feature_ranges = {
            'price_index': (0.8, 1.2),  # ±20% price
            'promo_flag': (0, 1),
            'trend_score': (0.3, 0.9)
        }

    baseline_pred = model.predict(base_features)[0]

    sensitivity = {}

    for feature, (min_val, max_val) in feature_ranges.items():
        if feature not in base_features.columns:
            continue

        # Test range of values
        test_values = np.linspace(min_val, max_val, 10)
        predictions = []

        for val in test_values:
            test_features = base_features.copy()
            test_features[feature] = val
            pred = model.predict(test_features)[0]
            predictions.append(pred)

        # Calculate elasticity
        value_range = max_val - min_val
        pred_range = max(predictions) - min(predictions)
        elasticity = (pred_range / baseline_pred) / (value_range / base_features[feature].values[0]) if baseline_pred > 0 else 0

        sensitivity[feature] = {
            'baseline_value': float(base_features[feature].values[0]),
            'baseline_prediction': float(baseline_pred),
            'test_values': test_values.tolist(),
            'predictions': [float(p) for p in predictions],
            'elasticity': float(elasticity),
            'min_prediction': float(min(predictions)),
            'max_prediction': float(max(predictions))
        }

    return sensitivity
