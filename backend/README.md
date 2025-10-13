# AFS Backend

Attribute Forecasting System - FastAPI Backend

## Setup

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run server
uvicorn app.main:app --reload
```

### Docker

```bash
docker build -t afs-backend .
docker run -p 8000:8000 -v $(pwd)/data:/app/data afs-backend
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/v1/predict` - Generate forecasts
- `POST /api/v1/train` - Train model
- `GET /api/v1/trends` - Get trend data
- `POST /api/v1/upload` - Upload data files

## Testing

```bash
pytest tests/
```
