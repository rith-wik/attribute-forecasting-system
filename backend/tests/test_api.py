import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_predict():
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
    assert "results" in data
    assert len(data["results"]) > 0

def test_train():
    request_data = {
        "backfill_days": 365,
        "retrain": True
    }
    response = client.post("/api/v1/train", json=request_data)

    # Should succeed if data is available, or return 400 if no data
    assert response.status_code in [200, 400]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        # Version should match expected format
        assert data["version"].startswith("afs-")

def test_trends():
    response = client.get("/api/v1/trends?region=AE&window_hours=24")
    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert isinstance(data["trends"], list)
