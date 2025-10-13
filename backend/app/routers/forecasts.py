from fastapi import APIRouter
from app.schemas import PredictRequest, PredictResponse
from app.services.model import ForecastService

router = APIRouter(tags=["forecasts"])

@router.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    svc = ForecastService()
    result = svc.predict(req)
    return result
