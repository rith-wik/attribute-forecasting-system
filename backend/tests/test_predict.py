"""Comprehensive tests for /predict endpoint and what-if scenarios"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)


def test_predict_basic():
    """Test basic prediction request"""
    request_data = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "skus": ["A1001"],
        "level": "attribute"
    }
    response = client.post("/api/v1/predict", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert "generated_at" in data
    assert "horizon_days" in data
    assert data["horizon_days"] == 7
    assert "results" in data
    assert len(data["results"]) > 0


def test_predict_30_day_horizon():
    """Test full 30-day forecast horizon"""
    request_data = {
        "horizon_days": 30,
        "store_ids": ["DXB01"],
        "level": "attribute"
    }
    response = client.post("/api/v1/predict", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["horizon_days"] == 30

    # Check first result has 30 daily forecasts
    if len(data["results"]) > 0:
        result = data["results"][0]
        assert "daily" in result
        assert len(result["daily"]) == 30


def test_predict_confidence_intervals():
    """Test that confidence intervals are provided and valid"""
    request_data = {
        "horizon_days": 14,
        "store_ids": ["DXB01"],
        "level": "attribute"
    }
    response = client.post("/api/v1/predict", json=request_data)
    assert response.status_code == 200

    data = response.json()
    result = data["results"][0]

    for day_forecast in result["daily"]:
        assert "forecast_units" in day_forecast
        assert "lo" in day_forecast
        assert "hi" in day_forecast

        # Verify intervals are valid
        forecast = day_forecast["forecast_units"]
        lo = day_forecast["lo"]
        hi = day_forecast["hi"]

        assert lo <= forecast <= hi, f"CI not valid: {lo} <= {forecast} <= {hi}"
        assert lo >= 0, "Lower bound should be non-negative"


def test_predict_ci_widening():
    """Test that confidence intervals widen with horizon"""
    request_data = {
        "horizon_days": 30,
        "store_ids": ["DXB01"],
        "level": "attribute"
    }
    response = client.post("/api/v1/predict", json=request_data)
    assert response.status_code == 200

    data = response.json()
    result = data["results"][0]
    daily = result["daily"]

    # Calculate CI width for first and last day
    day1_width = daily[0]["hi"] - daily[0]["lo"]
    day30_width = daily[-1]["hi"] - daily[-1]["lo"]

    # CI should widen (unless forecast drops significantly)
    assert day30_width >= day1_width * 0.8, "CI should widen with horizon"


def test_what_if_price_decrease():
    """Test what-if scenario with price decrease"""
    # Get baseline forecast
    baseline_request = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "skus": ["A1001"],
        "level": "attribute"
    }
    baseline_response = client.post("/api/v1/predict", json=baseline_request)
    baseline_data = baseline_response.json()
    baseline_forecast = baseline_data["results"][0]["daily"][0]["forecast_units"]

    # Apply price decrease
    what_if_request = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "skus": ["A1001"],
        "level": "attribute",
        "what_if": {
            "price_delta": -2.0  # $2 decrease
        }
    }
    what_if_response = client.post("/api/v1/predict", json=what_if_request)
    what_if_data = what_if_response.json()
    what_if_forecast = what_if_data["results"][0]["daily"][0]["forecast_units"]

    # Price decrease should increase demand
    assert what_if_forecast > baseline_forecast, \
        f"Price decrease should increase demand: {what_if_forecast} > {baseline_forecast}"


def test_what_if_price_increase():
    """Test what-if scenario with price increase"""
    # Get baseline forecast
    baseline_request = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "level": "attribute"
    }
    baseline_response = client.post("/api/v1/predict", json=baseline_request)
    baseline_data = baseline_response.json()
    baseline_forecast = baseline_data["results"][0]["daily"][0]["forecast_units"]

    # Apply price increase
    what_if_request = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "level": "attribute",
        "what_if": {
            "price_delta": 5.0  # $5 increase
        }
    }
    what_if_response = client.post("/api/v1/predict", json=what_if_request)
    what_if_data = what_if_response.json()
    what_if_forecast = what_if_data["results"][0]["daily"][0]["forecast_units"]

    # Price increase should decrease demand
    assert what_if_forecast < baseline_forecast, \
        f"Price increase should decrease demand: {what_if_forecast} < {baseline_forecast}"


def test_what_if_promo():
    """Test what-if scenario with promotion"""
    # Get baseline forecast
    baseline_request = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "level": "attribute"
    }
    baseline_response = client.post("/api/v1/predict", json=baseline_request)
    baseline_data = baseline_response.json()
    baseline_forecast = baseline_data["results"][0]["daily"][0]["forecast_units"]

    # Apply promo
    what_if_request = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "level": "attribute",
        "what_if": {
            "promo_flag": 1
        }
    }
    what_if_response = client.post("/api/v1/predict", json=what_if_request)
    what_if_data = what_if_response.json()
    what_if_forecast = what_if_data["results"][0]["daily"][0]["forecast_units"]

    # Promo should increase demand
    assert what_if_forecast > baseline_forecast, \
        f"Promo should increase demand: {what_if_forecast} > {baseline_forecast}"

    # Promo lift should be reasonable (10-40%)
    lift_pct = ((what_if_forecast - baseline_forecast) / baseline_forecast) * 100
    assert 10 <= lift_pct <= 40, f"Promo lift should be 10-40%, got {lift_pct:.1f}%"


def test_what_if_trend_boost():
    """Test what-if scenario with trend boost"""
    # Get baseline forecast
    baseline_request = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "level": "attribute"
    }
    baseline_response = client.post("/api/v1/predict", json=baseline_request)
    baseline_data = baseline_response.json()
    baseline_forecast = baseline_data["results"][0]["daily"][0]["forecast_units"]

    # Apply trend boost
    what_if_request = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "level": "attribute",
        "what_if": {
            "trend_boost": {
                "Black": 0.15  # 15% trend boost for Black color
            }
        }
    }
    what_if_response = client.post("/api/v1/predict", json=what_if_request)
    what_if_data = what_if_response.json()
    what_if_forecast = what_if_data["results"][0]["daily"][0]["forecast_units"]

    # Trend boost should increase demand
    assert what_if_forecast > baseline_forecast, \
        f"Trend boost should increase demand: {what_if_forecast} > {baseline_forecast}"


def test_what_if_combined():
    """Test combined what-if scenario (price + promo + trend)"""
    request_data = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "level": "attribute",
        "what_if": {
            "price_delta": -3.0,
            "promo_flag": 1,
            "trend_boost": {"Black": 0.2}
        }
    }
    response = client.post("/api/v1/predict", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert len(data["results"]) > 0

    # Combined effects should create significant lift
    forecast = data["results"][0]["daily"][0]["forecast_units"]
    assert forecast > 0, "Combined what-if should produce positive forecast"


def test_explainability_present():
    """Test that explainability data is included"""
    request_data = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "level": "attribute"
    }
    response = client.post("/api/v1/predict", json=request_data)
    data = response.json()

    result = data["results"][0]
    assert "explain" in result
    assert isinstance(result["explain"], dict)
    assert len(result["explain"]) > 0


def test_attribute_level_grouping():
    """Test that attribute-level predictions group by color/size/style"""
    request_data = {
        "horizon_days": 7,
        "level": "attribute"
    }
    response = client.post("/api/v1/predict", json=request_data)
    data = response.json()

    for result in data["results"]:
        assert "attributes" in result
        attrs = result["attributes"]
        assert "color" in attrs
        assert "size" in attrs
        assert "style" in attrs


def test_sku_level_prediction():
    """Test SKU-level prediction"""
    request_data = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "skus": ["A1001"],
        "level": "sku"
    }
    response = client.post("/api/v1/predict", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert len(data["results"]) > 0

    result = data["results"][0]
    assert "sku" in result
    assert result["sku"] == "A1001"


def test_multiple_stores():
    """Test prediction for multiple stores"""
    request_data = {
        "horizon_days": 7,
        "store_ids": ["DXB01", "DXB02"],
        "level": "attribute"
    }
    response = client.post("/api/v1/predict", json=request_data)
    data = response.json()

    # Should have results for multiple stores
    store_ids = {r["store_id"] for r in data["results"]}
    assert "DXB01" in store_ids or "DXB02" in store_ids


def test_forecast_non_negative():
    """Test that all forecasts are non-negative"""
    request_data = {
        "horizon_days": 30,
        "level": "attribute",
        "what_if": {
            "price_delta": 100.0  # Extreme price increase
        }
    }
    response = client.post("/api/v1/predict", json=request_data)
    data = response.json()

    for result in data["results"]:
        for day in result["daily"]:
            assert day["forecast_units"] >= 0, "Forecast should be non-negative"
            assert day["lo"] >= 0, "Lower bound should be non-negative"


def test_response_schema_compliance():
    """Test that response matches API schema"""
    request_data = {
        "horizon_days": 7,
        "store_ids": ["DXB01"],
        "level": "attribute"
    }
    response = client.post("/api/v1/predict", json=request_data)
    data = response.json()

    # Top-level fields
    assert "generated_at" in data
    assert "horizon_days" in data
    assert "results" in data

    # Result fields
    for result in data["results"]:
        assert "store_id" in result
        assert "sku" in result
        assert "attributes" in result
        assert "daily" in result
        assert "explain" in result

        # Daily forecast fields
        for day_forecast in result["daily"]:
            assert "date" in day_forecast
            assert "forecast_units" in day_forecast
            assert "lo" in day_forecast
            assert "hi" in day_forecast


def test_date_format():
    """Test that dates are in ISO format"""
    request_data = {
        "horizon_days": 3,
        "level": "attribute"
    }
    response = client.post("/api/v1/predict", json=request_data)
    data = response.json()

    # Check generated_at timestamp
    from datetime import datetime
    assert datetime.fromisoformat(data["generated_at"].replace('Z', '+00:00'))

    # Check daily forecast dates
    for result in data["results"]:
        for day in result["daily"]:
            assert datetime.fromisoformat(day["date"])


def test_horizon_limits():
    """Test various horizon day limits"""
    for horizon in [1, 7, 14, 30, 60]:
        request_data = {
            "horizon_days": horizon,
            "level": "attribute"
        }
        response = client.post("/api/v1/predict", json=request_data)
        assert response.status_code == 200

        data = response.json()
        if len(data["results"]) > 0:
            assert len(data["results"][0]["daily"]) == horizon
