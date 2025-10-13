# AFS Quick Start Guide - 5 Minutes

## Step 1: Install Prerequisites (One-Time Setup)

Open your WSL terminal and run:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip build-essential
```

Enter your password when prompted.

## Step 2: Run Setup Script

```bash
cd /mnt/c/Dev/AttributeForecastingSystem
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all required packages (FastAPI, XGBoost, pandas, etc.)
- Takes about 2-3 minutes

## Step 3: Start the Backend

```bash
./start_backend.sh
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Leave this terminal running.**

## Step 4: Test the API (New Terminal)

Open a new WSL terminal:

```bash
cd /mnt/c/Dev/AttributeForecastingSystem
./test_api.sh
```

This will test all endpoints and train the model.

## Step 5: Access the Application

Open your browser:

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Swagger UI**: http://localhost:8000/docs (interactive API testing)

## Quick Commands

### Start Backend
```bash
./start_backend.sh
```

### Test API
```bash
./test_api.sh
```

### Run Pytest Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

### Manual API Calls

**Health Check**:
```bash
curl http://localhost:8000/health
```

**Get Trends**:
```bash
curl http://localhost:8000/api/v1/trends
```

**Run Prediction**:
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "horizon_days": 7,
    "level": "attribute",
    "store_ids": ["DXB01"]
  }'
```

**Train Model**:
```bash
curl -X POST http://localhost:8000/api/v1/train \
  -H "Content-Type: application/json" \
  -d '{"force_retrain": true}'
```

**What-If Scenario (Price -$2)**:
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "horizon_days": 7,
    "level": "attribute",
    "store_ids": ["DXB01"],
    "what_if": {
      "price_delta": -2.0,
      "promo_flag": 1
    }
  }'
```

## Project Structure

```
/mnt/c/Dev/AttributeForecastingSystem/
├── setup.sh              ← Run this first
├── start_backend.sh      ← Start the server
├── test_api.sh           ← Test all endpoints
├── backend/
│   ├── app/             ← Source code
│   ├── tests/           ← 46+ tests
│   └── .venv/           ← Virtual environment (created by setup)
├── data/seed/           ← CSV data files
└── artifacts/           ← Trained models (created on first train)
```

## Common Issues

### "Permission denied" when running scripts
```bash
chmod +x setup.sh start_backend.sh test_api.sh
```

### "python3-venv not found"
```bash
sudo apt install python3-venv
```

### "Port 8000 already in use"
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

### "Module not found" errors
```bash
cd backend
source .venv/bin/activate
pip install fastapi uvicorn pandas numpy scikit-learn xgboost
```

## What's Next?

### Explore the API
- Open http://localhost:8000/docs
- Try different endpoints interactively
- View request/response schemas

### Run Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

Expected: 46+ tests passing

### Train Your Own Model
```bash
curl -X POST http://localhost:8000/api/v1/train \
  -H "Content-Type: application/json" \
  -d '{"force_retrain": true}'
```

### Try What-If Scenarios
Use the `/predict` endpoint with `what_if` parameters:
- `price_delta`: Change price (e.g., -2.0 for $2 discount)
- `promo_flag`: 0 or 1 (promotional campaign)
- `trend_boost`: {"Black": 0.3} (30% trend boost for Black)

### Read the Documentation
- **README.md** - Complete guide
- **ARCHITECTURE.md** - System architecture with diagrams
- **PATENT_CLAIMS.md** - Novel innovations
- **PROMPT_X_COMPLETE.md** - Implementation details

## Alternative: Docker Setup

If you prefer Docker (easier, production-ready):

1. Install Docker Desktop for Windows
2. Enable WSL 2 integration
3. Run:
   ```bash
   docker compose build
   docker compose up -d
   ```

Same access points (localhost:8000, localhost:5173)

## Support

For detailed troubleshooting:
- Check SETUP_INSTRUCTIONS.md
- Check RUN_LOCAL.md
- Review logs in terminal
- Check README.md

---

**TL;DR**: Run `./setup.sh` then `./start_backend.sh` then open http://localhost:8000/docs
