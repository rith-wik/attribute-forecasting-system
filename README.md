# Attribute Forecasting System (AFS)

Predict retail demand at attribute level (size, color, style) by store/region/channel with FastAPI + React dashboard.

## Features

- **Attribute-level forecasting**: Predict demand by size, color, and style combinations
- **Multi-modal fusion**: Combine historical sales, inventory, product metadata, and social trends
- **What-if analysis**: Test scenarios with price changes, promotions, and trend adjustments
- **Real-time dashboard**: React-based UI with interactive visualizations
- **Explainable AI**: Feature contribution analysis for each forecast
- **Dynamic data upload**: Web-based dataset upload with CSV/XLSX support and duplicate detection
- **Azure Storage integration**: Scalable cloud storage for datasets with local development mode

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Make (optional, for convenience commands)
- Python 3.11+ (for local development)
- Node.js 20+ (for local development)

### Running with Docker (Recommended)

**Option 1: Using Makefile (easiest)**

```bash
# View all available commands
make help

# Build and start all services
make build
make up

# Check service health
make health

# View logs
make logs           # All services
make logs-api       # API only
make logs-web       # Frontend only

# Train the model
make train

# Run a sample prediction
make predict

# Run tests
make test

# Stop services
make down

# Clean up everything
make prune
```

**Option 2: Using docker compose directly**

```bash
# Build images
docker compose build

# Start services in detached mode
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

**Access the application:**
- 🌐 Frontend Dashboard: http://localhost:5173
- 🔌 Backend API: http://localhost:8000
- 📚 API Documentation: http://localhost:8000/docs
- ❤️ Health Check: http://localhost:8000/health

### Local Development

#### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
afs/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   └── storage/     # Data access
│   └── tests/           # Backend tests
├── frontend/            # React frontend
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Page components
│       └── api/         # API client
├── data/
│   └── seed/           # Sample CSV data
└── docker-compose.yml
```

## API Endpoints

### Forecasting
- `POST /api/v1/predict` - Generate forecasts with optional what-if scenarios
- `POST /api/v1/train` - Train/retrain the forecasting model

### Data Management
- `GET /api/v1/trends` - Get social trend data
- `POST /api/v1/upload` - Upload dataset files (CSV/XLSX) with duplicate detection
- `GET /api/v1/datasets` - List all uploaded datasets
- `GET /api/v1/datasets/{type}/preview` - Preview dataset contents
- `DELETE /api/v1/datasets/{type}` - Delete a dataset

### Health
- `GET /health` - Service health check

## Testing

**With Docker (recommended):**
```bash
# Run all tests
make test

# Run tests in watch mode
make test-watch

# Run specific test file
docker compose exec api pytest tests/test_pipeline.py -v

# Run with coverage
docker compose exec api pytest tests/ --cov=app --cov-report=html
```

**Without Docker:**
```bash
cd backend
pytest tests/ -v
```

**Test Suites:**
- `test_pipeline.py` - Data pipeline and feature engineering (10+ tests)
- `test_training.py` - Model training and validation (14 tests)
- `test_predict.py` - Prediction endpoint and what-if scenarios (22 tests)

## Data Format

### products.csv
```csv
sku,style_code,style_desc,color_name,color_hex,size,category,price,image_path
A1001,ST-001,Slim Tee,Black,#000000,M,Tops,19.99,images/sample.jpg
```

### sales.csv
```csv
date,store_id,channel,sku,units_sold,promo_flag,price
2025-07-01,DXB01,store,A1001,6,0,19.99
```

### inventory.csv
```csv
date,store_id,sku,on_hand,on_order,lead_time_days
2025-07-01,DXB01,A1001,50,20,7
```

## Configuration

Copy `.env.example` to `.env` and adjust settings:

```bash
cp .env.example .env
```

**Environment Variables:**

Backend (`backend/.env`):
- `DATA_DIR` - Path to seed data (default: `/app/data/seed`)
- `ARTIFACTS_DIR` - Path to model artifacts (default: `/app/artifacts`)

Frontend (`frontend/.env`):
- `VITE_API_BASE` - Backend API URL (default: `http://localhost:8000/api/v1`)

## Deployment

### Production Deployment

**Docker Compose (Single Server):**

```bash
# Build production images
docker compose build

# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

**Docker Networking:**
- Services communicate via the `afs-network` bridge network
- Frontend depends on API health check before starting
- Auto-restart enabled with `unless-stopped` policy

**Volume Mounts:**
- `./data` → `/app/data` (persistent data storage)
- `./artifacts` → `/app/artifacts` (trained models)
- `./backend/app` → `/app/app` (hot-reload in development)
- `./frontend/src` → `/web/src` (hot-reload in development)

### Health Checks

**API Health:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

**Frontend Health:**
```bash
curl http://localhost:5173
# Expected: 200 OK
```

**Container Health:**
```bash
docker compose ps
# All services should show "healthy" status
```

## Troubleshooting

**Services won't start:**
```bash
# Check if ports are already in use
lsof -i :8000  # API port
lsof -i :5173  # Frontend port

# View detailed logs
docker compose logs -f api
docker compose logs -f web
```

**API returns 500 errors:**
```bash
# Check if data files exist
ls data/seed/

# Verify data format
head data/seed/products.csv
head data/seed/sales.csv

# Check API logs
docker compose logs api
```

**Frontend can't connect to API:**
```bash
# Verify VITE_API_BASE in frontend container
docker compose exec web env | grep VITE

# Test API from frontend container
docker compose exec web curl http://api:8000/health

# Check network connectivity
docker network inspect afs-network
```

**Model training fails:**
```bash
# Check if data is loaded
curl http://localhost:8000/api/v1/trends

# View training logs
docker compose logs api | grep -i train

# Verify artifacts directory exists
docker compose exec api ls -la /app/artifacts
```

**Hot-reload not working:**
```bash
# Ensure volume mounts are correct
docker compose config | grep volumes

# Restart services
docker compose restart
```

**Clean rebuild:**
```bash
# Remove everything and rebuild
make prune
make build
make up
```

## KPIs

- Attribute-level MAPE ≤ 30% on 4+ weeks backtest
- Forecast latency < 300ms (cached) for 100 SKUs
- Data refresh: daily
- Trend ingestion: hourly

## Tech Stack

**Backend:**
- FastAPI
- PyTorch Lightning
- scikit-learn
- XGBoost
- pandas
- Azure Blob Storage SDK

**Frontend:**
- React + TypeScript
- Vite
- Tailwind CSS
- Plotly/Chart.js

## Documentation

- **[Data Upload Feature](docs/DATA_UPLOAD_FEATURE.md)** - Guide for uploading and managing datasets
- **[Azure Storage Setup](docs/AZURE_STORAGE_SETUP.md)** - Configure Azure Blob Storage for production
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when running locally)

## License

MIT
