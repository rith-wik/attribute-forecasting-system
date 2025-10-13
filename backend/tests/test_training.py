"""Tests for model training and baseline forecaster"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.baseline_model import (
    SeasonalNaive,
    HybridForecaster,
    train_model,
    backtest_model
)
from app.services.data_pipeline import (
    load_seed,
    aggregate_by_attribute,
    add_moving_averages,
    add_promo_rate,
    add_price_index,
    add_seasonality_features,
    add_trend_signals
)


def create_sample_data(n_days=30):
    """Create sample time series data for testing"""
    dates = pd.date_range(start='2025-07-01', periods=n_days, freq='D')

    data = {
        'date': dates,
        'store_id': ['DXB01'] * n_days,
        'channel': ['store'] * n_days,
        'color_name': ['Black'] * n_days,
        'size': ['M'] * n_days,
        'style_desc': ['Slim Tee'] * n_days,
        'units_sold': np.random.poisson(5, n_days),  # Poisson distributed sales
        'promo_flag': np.random.binomial(1, 0.3, n_days),
        'price': 19.99,
        'category': ['Tops'] * n_days,
        'style_code': ['ST-001'] * n_days
    }

    df = pd.DataFrame(data)

    # Add features
    df = add_moving_averages(df, windows=[7, 28])
    df = add_promo_rate(df, window=7)
    df = add_price_index(df)
    df = add_seasonality_features(df)

    return df


def test_seasonal_naive_model():
    """Test SeasonalNaive forecaster"""
    # Create training data
    train_df = create_sample_data(21)  # 3 weeks
    X_train = train_df[['date']]
    y_train = train_df['units_sold']

    # Train model
    model = SeasonalNaive(seasonal_period=7)
    model.fit(X_train, y_train)

    # Make predictions
    test_df = create_sample_data(7)
    predictions = model.predict(test_df[['date']])

    assert len(predictions) == 7
    assert all(predictions >= 0)


def test_hybrid_forecaster_training():
    """Test HybridForecaster training"""
    df = create_sample_data(40)

    model = HybridForecaster(xgb_weight=0.7)
    model.fit(df, target_col='units_sold')

    # Check model was trained
    assert model.xgb_model is not None
    assert model.naive_model is not None
    assert len(model.feature_names) > 0


def test_hybrid_forecaster_prediction():
    """Test HybridForecaster predictions"""
    # Train on larger dataset
    train_df = create_sample_data(40)
    model = HybridForecaster(xgb_weight=0.7)
    model.fit(train_df, target_col='units_sold')

    # Predict on new data
    test_df = create_sample_data(7)
    predictions = model.predict(test_df)

    assert len(predictions) == 7
    assert all(predictions >= 0)  # Non-negative predictions
    assert np.isfinite(predictions).all()  # No NaN or inf


def test_hybrid_forecaster_save_load(tmp_path):
    """Test model serialization and deserialization"""
    df = create_sample_data(40)

    # Train and save
    model = HybridForecaster(xgb_weight=0.7)
    model.fit(df, target_col='units_sold')

    model_path = tmp_path / "test_model.pkl"
    model.save(str(model_path))

    assert model_path.exists()

    # Load and verify
    loaded_model = HybridForecaster.load(str(model_path))

    assert loaded_model.xgb_weight == model.xgb_weight
    assert loaded_model.feature_names == model.feature_names

    # Test predictions match
    test_df = create_sample_data(5)
    orig_preds = model.predict(test_df)
    loaded_preds = loaded_model.predict(test_df)

    np.testing.assert_array_almost_equal(orig_preds, loaded_preds, decimal=5)


def test_train_model_function():
    """Test the train_model function"""
    df = create_sample_data(50)

    model, metrics = train_model(df, target_col='units_sold')

    # Check model was returned
    assert model is not None
    assert isinstance(model, HybridForecaster)

    # Check metrics
    assert 'mae' in metrics
    assert 'mape' in metrics
    assert 'rmse' in metrics
    assert 'train_samples' in metrics
    assert 'test_samples' in metrics

    # MAE should be reasonable (not too high)
    assert metrics['mae'] >= 0
    assert metrics['mae'] < 100  # Sanity check

    # MAPE should be reasonable
    assert metrics['mape'] >= 0
    assert metrics['mape'] < 200  # Sanity check (200% is generous upper bound)


def test_train_model_mae_quality():
    """Test that model achieves reasonable MAE"""
    # Create more structured data for better predictions
    n_days = 60
    dates = pd.date_range(start='2025-07-01', periods=n_days, freq='D')

    # Create data with clear pattern (weekday effect + trend)
    units = []
    for i, date in enumerate(dates):
        base = 5 + (i * 0.1)  # Slight upward trend
        dow_effect = 2 if date.dayofweek < 5 else -1  # Weekday boost
        noise = np.random.normal(0, 0.5)
        units.append(max(0, base + dow_effect + noise))

    data = {
        'date': dates,
        'store_id': ['DXB01'] * n_days,
        'channel': ['store'] * n_days,
        'color_name': ['Black'] * n_days,
        'size': ['M'] * n_days,
        'style_desc': ['Slim Tee'] * n_days,
        'units_sold': units,
        'promo_flag': [0] * n_days,
        'price': 19.99,
        'category': ['Tops'] * n_days,
        'style_code': ['ST-001'] * n_days
    }

    df = pd.DataFrame(data)
    df = add_moving_averages(df, windows=[7, 28])
    df = add_promo_rate(df)
    df = add_price_index(df)
    df = add_seasonality_features(df)

    model, metrics = train_model(df, target_col='units_sold')

    # Model should achieve reasonable accuracy
    assert metrics['mae'] < 5.0  # MAE less than 5 units
    print(f"Model MAE: {metrics['mae']:.2f}, MAPE: {metrics['mape']:.2f}%")


def test_backtest_model():
    """Test backtesting functionality"""
    df = create_sample_data(50)

    # Train model
    model = HybridForecaster(xgb_weight=0.7)
    model.fit(df, target_col='units_sold')

    # Run backtest
    results = backtest_model(df, model, horizon_days=7)

    assert 'backtest_mae' in results or 'error' in results

    if 'backtest_mae' in results:
        assert results['backtest_mae'] >= 0
        assert 'backtest_mape' in results
        assert 'forecast_points' in results


def test_feature_importance():
    """Test feature importance extraction"""
    df = create_sample_data(40)

    model = HybridForecaster(xgb_weight=0.7)
    model.fit(df, target_col='units_sold')

    importance = model.get_feature_importance()

    assert isinstance(importance, dict)
    assert len(importance) > 0

    # All importance values should be non-negative
    for feat, imp in importance.items():
        assert imp >= 0
        assert feat in model.feature_names


def test_integration_with_real_data():
    """Integration test using real seed data if available"""
    from app.services.data_pipeline import load_seed

    products, sales, inv, trends = load_seed()

    if not sales.empty and not products.empty:
        # Aggregate and engineer features
        df = aggregate_by_attribute(sales, products)
        df = add_moving_averages(df, windows=[7, 28])
        df = add_promo_rate(df)
        df = add_price_index(df)
        df = add_seasonality_features(df)
        df = add_trend_signals(df, trends)

        # Train model
        model, metrics = train_model(df, target_col='units_sold')

        # Verify model was trained successfully
        assert model is not None
        assert 'mae' in metrics
        assert metrics['mae'] >= 0

        # Verify predictions work
        predictions = model.predict(df.head(5))
        assert len(predictions) == 5
        assert all(predictions >= 0)

        print(f"Real data training - MAE: {metrics['mae']:.2f}, MAPE: {metrics['mape']:.2f}%")
        print(f"Feature importance: {model.get_feature_importance()}")


def test_model_with_missing_features():
    """Test model handles missing features gracefully"""
    # Create minimal dataset
    df = pd.DataFrame({
        'date': pd.date_range('2025-07-01', periods=30),
        'store_id': ['DXB01'] * 30,
        'units_sold': np.random.poisson(5, 30),
        'ma_7d': np.random.uniform(4, 6, 30),
        'promo_flag': [0] * 30,
        'price_index': [1.0] * 30,
        'day_sin': np.sin(np.linspace(0, 2*np.pi, 30)),
        'day_cos': np.cos(np.linspace(0, 2*np.pi, 30)),
        'dow_sin': np.sin(np.linspace(0, 2*np.pi, 30)),
        'dow_cos': np.cos(np.linspace(0, 2*np.pi, 30))
    })

    model = HybridForecaster()
    model.fit(df, target_col='units_sold')

    predictions = model.predict(df.head(5))
    assert len(predictions) == 5
    assert all(predictions >= 0)


def test_zero_division_protection():
    """Test model handles edge cases like zero values"""
    df = create_sample_data(30)

    # Add some zeros to test robustness
    df.loc[df.index[:5], 'units_sold'] = 0

    model, metrics = train_model(df, target_col='units_sold')

    assert model is not None
    assert np.isfinite(metrics['mae'])
    assert np.isfinite(metrics['mape'])
