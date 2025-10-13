from fastapi import APIRouter, HTTPException
from app.schemas import TrainRequest, TrainResponse
from app.services.data_pipeline import load_seed, aggregate_by_attribute, aggregate_by_sku
from app.services.data_pipeline import (
    add_moving_averages, add_promo_rate, add_price_index,
    add_seasonality_features, add_stock_coverage, add_trend_signals
)
from app.services.baseline_model import train_model, backtest_model
from datetime import datetime, timedelta
import os

router = APIRouter(tags=["training"])

@router.post("/train", response_model=TrainResponse)
async def train(req: TrainRequest):
    """Train and persist forecasting model

    Args:
        req: Training request with backfill_days and retrain flag

    Returns:
        Training response with status, version, and metrics
    """
    try:
        # Load data
        products, sales, inv, trends = load_seed()

        if sales.empty:
            raise HTTPException(status_code=400, detail="No sales data available for training")

        # Filter to backfill window if specified
        if req.backfill_days and 'date' in sales.columns:
            cutoff_date = datetime.now() - timedelta(days=req.backfill_days)
            sales = sales[sales['date'] >= cutoff_date]

        # Engineer features at attribute level (more granular)
        df = aggregate_by_attribute(sales, products)

        if df.empty:
            raise HTTPException(status_code=400, detail="Failed to aggregate data")

        # Apply feature engineering pipeline
        df = add_moving_averages(df, windows=[7, 28])
        df = add_promo_rate(df, window=7)
        df = add_price_index(df)
        df = add_seasonality_features(df)
        df = add_trend_signals(df, trends)

        # Train model
        model, metrics = train_model(df, target_col='units_sold')

        # Perform backtesting
        backtest_results = backtest_model(df, model, horizon_days=7)
        metrics.update(backtest_results)

        # Generate version string
        version = f"afs-{datetime.now().strftime('%Y-%m-%d-%H%M')}"

        # Save model
        model_dir = "./artifacts"
        os.makedirs(model_dir, exist_ok=True)
        model_path = f"{model_dir}/{version}.pkl"
        model.save(model_path)

        # Save metadata
        metadata = {
            'version': version,
            'trained_at': datetime.now().isoformat(),
            'backfill_days': req.backfill_days,
            'metrics': metrics,
            'feature_importance': model.get_feature_importance()
        }

        import json
        with open(f"{model_dir}/{version}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        # Format response
        response_data = {
            'status': 'ok',
            'version': version,
            'model_path': model_path,
            'metrics': metrics
        }

        # Add optional fields to response if they exist
        if hasattr(TrainResponse, 'model_path'):
            return TrainResponse(**response_data)
        else:
            return TrainResponse(status=response_data['status'], version=response_data['version'])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")
