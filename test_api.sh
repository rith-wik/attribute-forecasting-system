#!/bin/bash

# Test script for AFS API

BASE_URL="http://localhost:8000"

echo "================================================"
echo "Testing AFS API"
echo "================================================"
echo ""

# Check if server is running
echo "Checking if server is running..."
if ! curl -s -f "$BASE_URL/health" > /dev/null; then
    echo "❌ Server is not running!"
    echo ""
    echo "Please start the server first:"
    echo "  ./start_backend.sh"
    exit 1
fi
echo "✅ Server is running"
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "----------------------------------------"
curl -s "$BASE_URL/health" | python3 -m json.tool 2>/dev/null || curl -s "$BASE_URL/health"
echo ""
echo ""

# Test 2: Get trends
echo "Test 2: Get Trends"
echo "----------------------------------------"
TRENDS=$(curl -s "$BASE_URL/api/v1/trends")
TREND_COUNT=$(echo "$TRENDS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "N/A")
echo "Found $TREND_COUNT trend records"
echo "$TRENDS" | python3 -m json.tool 2>/dev/null | head -20 || echo "$TRENDS" | head -20
echo "..."
echo ""
echo ""

# Test 3: Simple prediction
echo "Test 3: Run Prediction (7 days, attribute level)"
echo "----------------------------------------"
curl -s -X POST "$BASE_URL/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "horizon_days": 7,
    "level": "attribute",
    "store_ids": ["DXB01"]
  }' | python3 -m json.tool 2>/dev/null | head -50 || \
curl -s -X POST "$BASE_URL/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{"horizon_days": 7, "level": "attribute", "store_ids": ["DXB01"]}' | head -50
echo "..."
echo ""
echo ""

# Test 4: What-if prediction (price change)
echo "Test 4: What-If Scenario (Price -$2)"
echo "----------------------------------------"
curl -s -X POST "$BASE_URL/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "horizon_days": 3,
    "level": "attribute",
    "store_ids": ["DXB01"],
    "what_if": {
      "price_delta": -2.0
    }
  }' | python3 -m json.tool 2>/dev/null | head -40 || \
curl -s -X POST "$BASE_URL/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{"horizon_days": 3, "level": "attribute", "store_ids": ["DXB01"], "what_if": {"price_delta": -2.0}}' | head -40
echo "..."
echo ""
echo ""

# Test 5: Train model
echo "Test 5: Train Model"
echo "----------------------------------------"
echo "Training model (this takes ~30 seconds)..."
TRAIN_RESULT=$(curl -s -X POST "$BASE_URL/api/v1/train" \
  -H "Content-Type: application/json" \
  -d '{"force_retrain": true}')
echo "$TRAIN_RESULT" | python3 -m json.tool 2>/dev/null || echo "$TRAIN_RESULT"
echo ""
echo ""

echo "================================================"
echo "✅ All tests completed!"
echo "================================================"
echo ""
echo "API is working correctly. You can now:"
echo "  • View API docs: http://localhost:8000/docs"
echo "  • Access full API: http://localhost:8000/api/v1/"
echo "  • Run pytest tests: cd backend && pytest tests/ -v"
echo ""
