AFS – Claude‑Ready Prompt Pack (Attribute Forecasting System)
Use this pack verbatim with Claude (or any coding copilot). It contains requirements, file tree, data schemas, API contracts, code stubs, UI spec, and deployment steps to generate a working MVP.
________________________________________
0) Product Brief (paste to Claude)
Project: Attribute Forecasting System (AFS) – MVP
Goal: Predict retail demand at attribute level (size, color, style) by store/region/channel and expose via FastAPI + React dashboard. Fuse historical sales, inventory, product metadata, optional social trend signals, and optional image embeddings.
Non‑goals: Advanced AutoML, perfect accuracy, complex MDM integrations. Focus on clean, modular MVP.
Why: Foundational component for a patent family around attribute‑level forecasting, multi‑modal fusion, and real‑time trend adjustment.
KPIs (MVP): - Attribute‑level MAPE ≤ 30% on 4+ weeks backtest - Forecast latency < 300ms (cached) for 100 SKUs - Data refresh daily; trend ingestion hourly (mock OK)
Tech stack: Python 3.11, FastAPI, PyTorch Lightning, scikit‑learn, pandas, PostgreSQL (or DuckDB for dev), Redis (optional cache), React + Vite + Tailwind, Plotly/Chart.js.
________________________________________
1) Repository Layout (ask Claude to create)
afs/
  backend/
    app/
      __init__.py
      main.py
      config.py
      schemas.py
      deps.py
      routers/
        forecasts.py
        training.py
        trends.py
        uploads.py
      services/
        data_pipeline.py
        feature_fusion.py
        model.py
        explain.py
        trend_ingest.py
      storage/
        db.py
        fs.py
    tests/
      test_api.py
      test_pipeline.py
    Dockerfile
    pyproject.toml
    README.md
  frontend/
    index.html
    src/
      main.tsx
      App.tsx
      api/client.ts
      components/
        AttributeHeatmap.tsx
        ForecastTable.tsx
        WhatIfPanel.tsx
        TrendSpark.tsx
        KPI.tsx
      pages/
        Dashboard.tsx
        SKUDetail.tsx
    vite.config.ts
    package.json
    tsconfig.json
    postcss.config.js
    tailwind.config.js
    Dockerfile
  data/
    seed/
      products.csv
      sales.csv
      inventory.csv
      social_trends.csv
      images/
        sample_*.jpg
  docker-compose.yml
  Makefile
  .env.example
________________________________________
2) Data Model & Seed Schemas
2.1 products.csv
Columns: - sku (str) - style_code (str) - style_desc (str) - color_name (str) - color_hex (str, like #112233) - size (str, XS…XXL / EU sizes) - category (str) - price (float) - image_path (str, optional)
Example rows:
sku,style_code,style_desc,color_name,color_hex,size,category,price,image_path
A1001,ST-001,Slim Tee,Black,#000000,M,Tops,19.99,images/sample_tee_black.jpg
A1002,ST-001,Slim Tee,Black,#000000,L,Tops,19.99,images/sample_tee_black.jpg
A1203,DR-010,Day Dress,Flame,#E4572E,S,Dresses,59.00,images/sample_dress_red.jpg
2.2 sales.csv
•	date (YYYY-MM-DD)
•	store_id (str)
•	channel (str: store/online)
•	sku (str)
•	units_sold (int)
•	promo_flag (0/1)
•	price (float, actual selling price)
date,store_id,channel,sku,units_sold,promo_flag,price
2025-07-01,DXB01,store,A1001,6,0,19.99
2025-07-01,DXB01,store,A1002,4,1,17.99
2025-07-02,DXB02,online,A1203,3,0,59.00
2.3 inventory.csv
•	date
•	store_id
•	sku
•	on_hand (int)
•	on_order (int)
•	lead_time_days (int)
2.4 social_trends.csv (mock OK)
•	timestamp (ISO)
•	region (str)
•	channel (str e.g., instagram, tiktok)
•	color_name (str)
•	style_keyword (str)
•	trend_score (float 0–1)
timestamp,region,channel,color_name,style_keyword,trend_score
2025-07-01T10:00:00Z,AE,instagram,Black,slim tee,0.63
2025-07-02T10:00:00Z,AE,tiktok,Flame,day dress,0.81
Optional: add weather, holidays, returns.
________________________________________
3) Database Notes
•	For quick start, use DuckDB/Parquet for offline features; upgrade to Postgres for API state.
•	Create materialized views:
o	mv_attribute_sales (aggregate by date, region, attribute triplet size–color–style)
o	mv_stock_positions (on_hand + on_order projections)
________________________________________
4) API Contracts (FastAPI)
4.1 POST /api/v1/predict
Request JSON:
{
  "horizon_days": 30,
  "store_ids": ["DXB01", "DXB02"],
  "skus": ["A1001","A1002"],
  "level": "attribute",          // "sku" | "attribute"
  "what_if": {                    // optional
    "price_delta": -2.0,
    "promo_flag": 1,
    "trend_boost": {"Black": 0.1}
  }
}
Response JSON:
{
  "generated_at": "2025-10-06T14:00:00Z",
  "horizon_days": 30,
  "results": [
    {
      "store_id": "DXB01",
      "sku": "A1001",
      "attributes": {"color": "Black", "size": "M", "style": "Slim Tee"},
      "daily": [
        {"date": "2025-10-07", "forecast_units": 0.9, "lo": 0.6, "hi": 1.2}
      ],
      "explain": {"price": -0.12, "trend_Black": 0.25, "seasonality": 0.18}
    }
  ]
}
4.2 POST /api/v1/train
{ "backfill_days": 365, "retrain": true }
Response: { "status": "ok", "version": "afs-2025-10-06-01" }
4.3 GET /api/v1/trends?region=AE&window_hours=24
Returns top colors/styles with scores.
4.4 POST /api/v1/upload
Multipart CSVs: products.csv, sales.csv, inventory.csv, optional social_trends.csv.
________________________________________
5) Backend Code Stubs (have Claude fill in)
5.1 app/main.py
from fastapi import FastAPI
from app.routers import forecasts, training, trends, uploads

app = FastAPI(title="AFS API", version="0.1.0")
app.include_router(forecasts.router, prefix="/api/v1")
app.include_router(training.router, prefix="/api/v1")
app.include_router(trends.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}
5.2 app/routers/forecasts.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.services.model import ForecastService

router = APIRouter(tags=["forecasts"])

class WhatIf(BaseModel):
    price_delta: Optional[float] = None
    promo_flag: Optional[int] = None
    trend_boost: Optional[Dict[str, float]] = None

class PredictRequest(BaseModel):
    horizon_days: int = 30
    store_ids: Optional[List[str]] = None
    skus: Optional[List[str]] = None
    level: str = "attribute"
    what_if: Optional[WhatIf] = None

@router.post("/predict")
async def predict(req: PredictRequest):
    svc = ForecastService()
    result = svc.predict(req)
    return result
5.3 app/services/model.py
from dataclasses import dataclass
from typing import Dict, Any
from app.services.data_pipeline import load_features
from app.services.explain import explain_contribs

@dataclass
class ForecastService:
    model_path: str = "./artifacts/model.pt"

    def predict(self, req) -> Dict[str, Any]:
        X = load_features(req)
        # TODO: load torch model; for MVP use baseline (seasonal naive + xgboost)
        yhat = self._baseline_forecast(X, req.horizon_days)
        resp = self._format_response(yhat)
        return resp

    def _baseline_forecast(self, X, horizon):
        # stub: simple moving average + trend_boost
        return X

    def _format_response(self, yhat):
        # convert to API schema
        return {
            "generated_at": "TODO",
            "horizon_days": 30,
            "results": []
        }
5.4 app/services/data_pipeline.py
import pandas as pd
from typing import Any

DATA_DIR = "./data/seed"

def load_seed():
    products = pd.read_csv(f"{DATA_DIR}/products.csv")
    sales = pd.read_csv(f"{DATA_DIR}/sales.csv", parse_dates=["date"])
    inv = pd.read_csv(f"{DATA_DIR}/inventory.csv", parse_dates=["date"])
    try:
        trends = pd.read_csv(f"{DATA_DIR}/social_trends.csv", parse_dates=["timestamp"])
    except FileNotFoundError:
        trends = pd.DataFrame()
    return products, sales, inv, trends

def load_features(req: Any):
    products, sales, inv, trends = load_seed()
    # join, aggregate by attribute triplet; engineer features (7/28-day MA, seasonality, promo)
    # return feature frame ready for model
    return {}
5.5 app/services/feature_fusion.py
# color hex → HSV; style_desc → text embedding; optional image → CLIP embedding
# fuse into numeric feature vector per attribute group
5.6 app/services/trend_ingest.py
# mock trend generator; in prod, connect to APIs and normalise to [0,1]
5.7 app/services/explain.py
# return per-feature contributions for explainability (placeholder)
________________________________________
6) Frontend Spec (React + Tailwind)
Pages: - Dashboard (default): - KPIs: Avg MAPE, Top Rising Color, Stockout Risk Count - Filters: Date range, Region, Store cluster, Category - Components: - AttributeHeatmap (rows: size; cols: color; cell: forecast lift %; segmented by style) - TrendSpark (top trending colors/styles, 7‑day sparkline) - ForecastTable (store × SKU × attribute with daily forecast and CI) - WhatIfPanel (price Δ, promo toggle, trend boost per color) - SKUDetail: Drill‑down chart with historical vs forecast, explainability bars (feature contributions).
API client: /api/client.ts with typed methods for /predict, /train, /trends.
UX notes: - Edge cases: no data, sparse SKUs, missing colors; show skeleton loaders, empty‑state cards. - Accessibility: keyboard‑navigable tables, aria‑labels for charts.
________________________________________
7) Docker & Compose
7.1 backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir uv && uv pip install -r <(python - <<EOF
from tomllib import load;print('\n'.join(load(open('pyproject.toml','rb'))['project']['dependencies']))
EOF
)
COPY app /app/app
COPY ../data /app/data
EXPOSE 8000
CMD ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
7.2 frontend/Dockerfile
FROM node:20-alpine
WORKDIR /web
COPY package.json package-lock.json /web/
RUN npm ci
COPY . /web
EXPOSE 5173
CMD ["npm","run","dev","--","--host"]
7.3 docker-compose.yml
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    volumes:
      - ./data:/app/data
  web:
    build: ./frontend
    ports: ["5173:5173"]
    environment:
      - VITE_API_BASE=http://localhost:8000/api/v1
    depends_on: [api]
________________________________________
8) Makefile & Scripts
.PHONY: setup dev test
setup:
    python -m venv .venv && . .venv/bin/activate && pip install -e ./backend

dev:
    docker compose up --build

test:
    pytest -q backend/tests
________________________________________
9) Testing (pytest)
•	test_pipeline.py: verify feature engineering on seed data
•	test_api.py: spin up TestClient, call /predict, assert shape
•	Add fixtures for tiny CSVs
________________________________________
10) Deployment Notes
•	Local: docker compose up
•	Cloud (MVP): Single VM (EC2) running compose; serve web via Nginx; attach S3 for data; add basic auth
•	Observability: FastAPI /metrics, request logs, model version in response
________________________________________
11) Patent‑Readiness Hooks (document during build)
•	Architecture diagrams (data → fusion → model → API → UI)
•	Evidence of dynamic attribute embeddings (color HSV + style text/image vectors)
•	Real‑time trend adjustment loop (trend_boost integration path)
•	Explainability: per‑attribute feature contributions
•	Edge‑deploy note: quantization path for on‑device inference (stub OK)
________________________________________
12) Initial Prompts for Claude (copy/paste in order)
Prompt A — Generate project skeleton & files > Create the file tree described in Section 1. Populate each file with minimal runnable code from Sections 5–7. Add npm & Python dependencies. Provide the exact shell commands to run backend and frontend locally. Ensure /health returns {status: "ok"}.
Prompt B — Implement data pipeline > Implement data_pipeline.load_features(): read seed CSVs, aggregate sales by date–store–SKU and by attribute triplet (size, color, style). Engineer features: 7/28‑day moving averages, promo rate, price index, seasonality (sin/cos), stock coverage (on_hand / 7‑day avg sales). Return frames aligned for model.
Prompt C — Baseline model & training > In model.py, implement a baseline hybrid model: XGBoost for tabular features + seasonal naive backstop. Add /train to persist model artifact with version string. Add unit tests that train on seed data and assert a non‑trivial MAE.
Prompt D — /predict & explainability > Implement /predict to score horizons up to 30 days; support what_if price_delta, promo_flag, and color trend boost. In explain.py, return simple SHAP‑like attributions (model‑agnostic permutation importance is fine for MVP). Ensure response matches the contract.
Prompt E — Frontend dashboard > Build Dashboard with filters, AttributeHeatmap, ForecastTable, TrendSpark, and WhatIfPanel. Wire to API. Use Tailwind for layout and Plotly/Chart.js for charts. Include loading states and empty states.
Prompt F — Docker & compose > Finalise Dockerfiles and docker-compose.yml. Provide commands to build/run, and a short README with screenshots placeholders.
Prompt G — Patent artifacts > Output a docs/ folder with architecture diagrams (Mermaid), a dataflow diagram, and a 1‑page writeup highlighting the novel elements suitable for a provisional filing appendix.
________________________________________
13) Acceptance Checklist
☐	docker compose up serves API on :8000, web on :5173
☐	/api/v1/predict returns forecasts with CI for two sample SKUs
☐	Heatmap renders attribute lift (%) over baseline
☐	What‑if controls adjust forecast
☐	Backtests for last 4 weeks produce MAPE metric
☐	Docs folder contains diagrams & patent notes
________________________________________
14) Nice‑to‑Have Extensions
•	Add CLIP text+image embeddings for style/color vectors (feature_fusion.py)
•	Redis cache for hot queries
•	MLflow model registry
•	Role‑based auth for merch vs planner
________________________________________
End of Prompt Pack
