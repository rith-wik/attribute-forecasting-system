# AFS Model Training Guide

## Quick Start

### Train a New Model

```bash
curl -X POST http://localhost:8000/api/v1/train \
  -H "Content-Type: application/json" \
  -d '{
    "backfill_days": 365,
    "retrain": true
  }'
```

**Response**:
```json
{
  "status": "ok",
  "version": "afs-2025-10-06-1430"
}
```

### Use the Trained Model

The trained model is automatically loaded and used for predictions:

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "horizon_days": 30,
    "store_ids": ["DXB01"],
    "level": "attribute"
  }'
```

## Model Architecture

### Hybrid Forecaster
Combines two complementary approaches:

1. **XGBoost (70% weight)**
   - Gradient boosted trees
   - Captures complex feature interactions
   - Uses 14+ engineered features

2. **Seasonal Naive (30% weight)**
   - Same-day-of-week from last week
   - Provides stable baseline
   - Handles sparse data well

### Why Hybrid?
- XGBoost alone can overfit on sparse data
- Seasonal Naive provides robust floor
- Weighted combination reduces variance
- Better handles edge cases

## Training Process

```
1. Load Data
   ├─ products.csv
   ├─ sales.csv
   ├─ inventory.csv
   └─ social_trends.csv

2. Filter (backfill_days)
   └─ Keep only last N days

3. Aggregate by Attribute
   └─ Group by color, size, style

4. Engineer Features
   ├─ Moving averages (7d, 28d)
   ├─ Promo rate
   ├─ Price index
   ├─ Seasonality (sin/cos)
   ├─ Stock coverage
   └─ Trend signals

5. Train Model
   ├─ 80% train / 20% test split
   └─ Fit HybridForecaster

6. Calculate Metrics
   ├─ MAE (Mean Absolute Error)
   ├─ MAPE (Mean Absolute Percentage Error)
   └─ RMSE (Root Mean Squared Error)

7. Backtest
   └─ 4-week rolling validation

8. Save Artifacts
   ├─ Model: artifacts/afs-{timestamp}.pkl
   └─ Metadata: artifacts/afs-{timestamp}_metadata.json

9. Return Version
```

## Model Files

### Model Binary (`.pkl`)
- Complete model state
- XGBoost model
- Seasonal Naive model
- Feature names
- Weights and configuration

### Metadata JSON
```json
{
  "version": "afs-2025-10-06-1430",
  "trained_at": "2025-10-06T14:30:15.123Z",
  "backfill_days": 365,
  "metrics": {
    "mae": 2.34,
    "mape": 24.5,
    "rmse": 3.12,
    "train_samples": 120,
    "test_samples": 30,
    "backtest_mae": 2.51,
    "backtest_mape": 26.3
  },
  "feature_importance": {
    "ma_7d": 0.35,
    "trend_score": 0.22,
    "dow_sin": 0.10,
    "dow_cos": 0.08,
    "promo_rate_7d": 0.12,
    "ma_28d": 0.08,
    "price_index": 0.05
  }
}
```

## Expected Performance

### Metrics
- **MAE**: 2-4 units (Target: < 5)
- **MAPE**: 20-30% (Target: ≤ 30%)
- **Training time**: 2-5 seconds (on seed data)
- **Prediction latency**: 50-100ms per request

### Quality Assertions
The test suite includes:
```python
assert metrics['mae'] < 5.0  # MAE less than 5 units
```

## Feature Importance

Typical feature importance ranking:

| Feature | Importance | Description |
|---------|-----------|-------------|
| ma_7d | 0.35 | 7-day moving average |
| trend_score | 0.22 | Social media trends |
| dow_sin/cos | 0.18 | Day of week |
| promo_rate_7d | 0.12 | Promotion intensity |
| ma_28d | 0.08 | 28-day moving average |
| price_index | 0.05 | Relative price |

## Python API

### Train Model Programmatically

```python
from app.services.baseline_model import train_model, HybridForecaster
from app.services.data_pipeline import load_features

# Load and prepare data
feature_data = load_features(request)
df = feature_data['attribute_features']

# Train model
model, metrics = train_model(df, target_col='units_sold')

print(f"MAE: {metrics['mae']:.2f}")
print(f"MAPE: {metrics['mape']:.2f}%")

# Save model
model.save("./artifacts/my_model.pkl")
```

### Load and Use Model

```python
from app.services.baseline_model import HybridForecaster

# Load trained model
model = HybridForecaster.load("./artifacts/afs-2025-10-06-1430.pkl")

# Make predictions
predictions = model.predict(df)

# Get feature importance
importance = model.get_feature_importance()
```

## Backtesting

The training process includes automatic backtesting:

```python
from app.services.baseline_model import backtest_model

results = backtest_model(
    df=historical_data,
    model=trained_model,
    horizon_days=7
)

print(f"Backtest MAE: {results['backtest_mae']:.2f}")
print(f"Backtest MAPE: {results['backtest_mape']:.2f}%")
```

**Process**:
1. Takes last 4 weeks of data
2. For each day, predict next 7 days
3. Compare predictions vs actuals
4. Calculate rolling MAE and MAPE

## Retraining Strategy

### When to Retrain
- Weekly: to capture recent trends
- After major promotions
- When MAPE degrades > 5%
- After adding new SKUs

### Automated Retraining
Add to cron:
```bash
# Retrain weekly on Sunday at 2am
0 2 * * 0 curl -X POST http://localhost:8000/api/v1/train \
  -H "Content-Type: application/json" \
  -d '{"backfill_days": 365, "retrain": true}'
```

## Troubleshooting

### Model Not Loading
```
Error: Failed to load model from ./artifacts/afs-xxx.pkl
```

**Solution**:
- Check if file exists
- Verify pickle compatibility
- Try retraining

### High MAE/MAPE
```
MAE: 15.3, MAPE: 65%
```

**Possible causes**:
- Insufficient training data (< 30 days)
- Missing features (check feature columns)
- Data quality issues (outliers, nulls)

**Solutions**:
- Increase backfill_days
- Check data pipeline logs
- Validate seed CSV files

### Training Fails
```
HTTPException: Training failed: Failed to aggregate data
```

**Solution**:
- Verify CSV files exist in `data/seed/`
- Check CSV format matches schema
- Ensure at least 2 weeks of data

## Advanced Configuration

### Adjust Hybrid Weights
```python
# More weight to XGBoost (80%)
model = HybridForecaster(xgb_weight=0.8)

# More weight to Seasonal Naive (50/50)
model = HybridForecaster(xgb_weight=0.5)
```

### XGBoost Hyperparameters
Edit `baseline_model.py`:
```python
self.xgb_model = xgb.XGBRegressor(
    n_estimators=200,      # Increase trees
    max_depth=7,           # Deeper trees
    learning_rate=0.05,    # Slower learning
    subsample=0.9,
    colsample_bytree=0.9
)
```

## Next Steps

- **Prompt D**: Enhanced explainability with SHAP-like attributions
- **Prompt E**: Frontend integration for model metrics
- **Prompt F**: Production deployment with MLflow
- **Prompt G**: Patent documentation

---

For more details, see:
- [PROMPT_C_COMPLETE.md](./PROMPT_C_COMPLETE.md) - Full implementation details
- [PROGRESS.md](./PROGRESS.md) - Overall project progress
