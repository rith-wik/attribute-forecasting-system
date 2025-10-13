"""Baseline hybrid forecasting model: XGBoost + Seasonal Naive"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import pickle
import os
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
import xgboost as xgb


class SeasonalNaive:
    """Seasonal naive forecaster - uses same weekday from previous week"""

    def __init__(self, seasonal_period: int = 7):
        self.seasonal_period = seasonal_period
        self.historical_data = None

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Store historical data for naive forecasting"""
        self.historical_data = pd.DataFrame({
            'date': X['date'] if 'date' in X.columns else pd.to_datetime(X.index),
            'y': y
        })
        self.historical_data['dow'] = self.historical_data['date'].dt.dayofweek
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict using seasonal naive (last week's same day)"""
        if self.historical_data is None:
            return np.ones(len(X))

        predictions = []
        for idx, row in X.iterrows():
            date = row.get('date', datetime.now())
            dow = pd.to_datetime(date).dayofweek

            # Find same day of week from history
            same_dow = self.historical_data[self.historical_data['dow'] == dow]
            if not same_dow.empty:
                # Use most recent value for this day of week
                pred = same_dow.iloc[-1]['y']
            else:
                # Fallback to overall mean
                pred = self.historical_data['y'].mean()

            predictions.append(pred)

        return np.array(predictions)


class HybridForecaster:
    """Hybrid model combining XGBoost and Seasonal Naive"""

    def __init__(self, xgb_weight: float = 0.7):
        """
        Args:
            xgb_weight: Weight for XGBoost predictions (0-1),
                       remainder goes to seasonal naive
        """
        self.xgb_weight = xgb_weight
        self.naive_weight = 1.0 - xgb_weight

        # XGBoost model with reasonable defaults
        self.xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective='reg:squarederror'
        )

        self.naive_model = SeasonalNaive(seasonal_period=7)
        self.feature_names = []
        self.scaler_params = {}

    def _prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, list]:
        """Extract and prepare features for modeling"""
        feature_cols = [
            'ma_7d', 'ma_28d', 'promo_flag', 'promo_rate_7d',
            'price_index', 'day_sin', 'day_cos', 'dow_sin', 'dow_cos'
        ]

        # Add optional features if present
        optional_cols = ['stock_coverage', 'incoming_coverage', 'trend_score']
        for col in optional_cols:
            if col in df.columns:
                feature_cols.append(col)

        # Filter to available columns
        feature_cols = [col for col in feature_cols if col in df.columns]

        if not feature_cols:
            raise ValueError("No valid feature columns found in dataframe")

        # Extract feature matrix
        X = df[feature_cols].copy()

        # Fill NaN values with 0
        X = X.fillna(0)

        return X.values, feature_cols

    def fit(self, df: pd.DataFrame, target_col: str = 'units_sold'):
        """Train the hybrid model

        Args:
            df: DataFrame with engineered features
            target_col: Name of target column to predict
        """
        if df.empty or target_col not in df.columns:
            raise ValueError(f"DataFrame empty or missing target column '{target_col}'")

        # Prepare features and target
        X, self.feature_names = self._prepare_features(df)
        y = df[target_col].values

        # Train XGBoost
        self.xgb_model.fit(X, y)

        # Train Seasonal Naive (needs date info)
        self.naive_model.fit(df, pd.Series(y))

        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Generate predictions using hybrid approach

        Args:
            df: DataFrame with same features as training data

        Returns:
            Array of predictions
        """
        if df.empty:
            return np.array([])

        # Get predictions from both models
        X, _ = self._prepare_features(df)
        xgb_preds = self.xgb_model.predict(X)
        naive_preds = self.naive_model.predict(df)

        # Combine with weighted average
        hybrid_preds = (self.xgb_weight * xgb_preds +
                       self.naive_weight * naive_preds)

        # Ensure non-negative predictions
        hybrid_preds = np.maximum(hybrid_preds, 0)

        return hybrid_preds

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from XGBoost model"""
        if not self.feature_names:
            return {}

        importance = self.xgb_model.feature_importances_
        return dict(zip(self.feature_names, importance))

    def save(self, filepath: str):
        """Save model to disk"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        model_data = {
            'xgb_model': self.xgb_model,
            'naive_model': self.naive_model,
            'xgb_weight': self.xgb_weight,
            'naive_weight': self.naive_weight,
            'feature_names': self.feature_names,
            'scaler_params': self.scaler_params,
            'trained_at': datetime.utcnow().isoformat()
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

    @classmethod
    def load(cls, filepath: str) -> 'HybridForecaster':
        """Load model from disk"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        model = cls(xgb_weight=model_data['xgb_weight'])
        model.xgb_model = model_data['xgb_model']
        model.naive_model = model_data['naive_model']
        model.feature_names = model_data['feature_names']
        model.scaler_params = model_data.get('scaler_params', {})

        return model


def train_model(df: pd.DataFrame, target_col: str = 'units_sold') -> Tuple[HybridForecaster, Dict[str, float]]:
    """Train a hybrid forecasting model and return metrics

    Args:
        df: DataFrame with engineered features and target
        target_col: Name of target column

    Returns:
        Trained model and dictionary of metrics
    """
    if df.empty:
        raise ValueError("Cannot train on empty dataframe")

    # Sort by date for proper train/test split
    if 'date' in df.columns:
        df = df.sort_values('date')

    # Train/test split (80/20)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    # Train model
    model = HybridForecaster(xgb_weight=0.7)
    model.fit(train_df, target_col)

    # Evaluate on test set
    if len(test_df) > 0:
        y_true = test_df[target_col].values
        y_pred = model.predict(test_df)

        mae = mean_absolute_error(y_true, y_pred)

        # Calculate MAPE with protection against zero division
        mask = y_true != 0
        if mask.sum() > 0:
            mape = mean_absolute_percentage_error(y_true[mask], y_pred[mask]) * 100
        else:
            mape = 0.0

        # RMSE
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

        metrics = {
            'mae': float(mae),
            'mape': float(mape),
            'rmse': float(rmse),
            'train_samples': len(train_df),
            'test_samples': len(test_df)
        }
    else:
        # No test data, return training metrics
        y_true = train_df[target_col].values
        y_pred = model.predict(train_df)
        mae = mean_absolute_error(y_true, y_pred)

        metrics = {
            'mae': float(mae),
            'mape': 0.0,
            'rmse': float(mae),
            'train_samples': len(train_df),
            'test_samples': 0
        }

    return model, metrics


def backtest_model(df: pd.DataFrame, model: HybridForecaster,
                  horizon_days: int = 7, target_col: str = 'units_sold') -> Dict[str, Any]:
    """Perform backtesting on historical data

    Args:
        df: Full historical dataframe
        model: Trained model
        horizon_days: Forecast horizon in days
        target_col: Target column name

    Returns:
        Dictionary with backtest results and metrics
    """
    if 'date' not in df.columns:
        return {'error': 'Date column required for backtesting'}

    df = df.sort_values('date')

    # Take last N weeks for backtesting
    test_start_idx = len(df) - (horizon_days * 4)  # 4 weeks of backtesting
    if test_start_idx < horizon_days:
        test_start_idx = horizon_days

    forecasts = []
    actuals = []

    # Rolling forecast
    for i in range(test_start_idx, len(df) - horizon_days):
        # Use data up to point i for prediction
        historical = df.iloc[:i]

        # Predict next horizon_days
        future = df.iloc[i:i+horizon_days]
        preds = model.predict(future)

        forecasts.extend(preds)
        actuals.extend(future[target_col].values)

    # Calculate backtest metrics
    if len(actuals) > 0:
        forecasts = np.array(forecasts)
        actuals = np.array(actuals)

        mae = mean_absolute_error(actuals, forecasts)

        mask = actuals != 0
        if mask.sum() > 0:
            mape = mean_absolute_percentage_error(actuals[mask], forecasts[mask]) * 100
        else:
            mape = 0.0

        return {
            'backtest_mae': float(mae),
            'backtest_mape': float(mape),
            'forecast_points': len(actuals),
            'horizon_days': horizon_days
        }

    return {'error': 'Insufficient data for backtesting'}
