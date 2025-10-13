from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

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

class DailyForecast(BaseModel):
    date: str
    forecast_units: float
    lo: float
    hi: float

class ForecastResult(BaseModel):
    store_id: str
    sku: str
    attributes: Dict[str, str]
    daily: List[DailyForecast]
    explain: Dict[str, float]

class PredictResponse(BaseModel):
    generated_at: str
    horizon_days: int
    results: List[ForecastResult]

class TrainRequest(BaseModel):
    backfill_days: int = 365
    retrain: bool = True

class TrainResponse(BaseModel):
    status: str
    version: str
