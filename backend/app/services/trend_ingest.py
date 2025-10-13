"""Trend ingestion service"""
import random
from datetime import datetime
from typing import Dict, List

def generate_mock_trends(region: str = "AE", count: int = 5) -> List[Dict]:
    """Generate mock trend data"""
    colors = ["Black", "White", "Flame", "Navy", "Olive"]
    styles = ["slim tee", "day dress", "cargo pants", "oversized hoodie"]

    trends = []
    for i in range(count):
        trends.append({
            "timestamp": datetime.utcnow().isoformat(),
            "region": region,
            "channel": random.choice(["instagram", "tiktok", "pinterest"]),
            "color_name": random.choice(colors),
            "style_keyword": random.choice(styles),
            "trend_score": round(random.uniform(0.3, 1.0), 2)
        })

    return trends

def normalize_trend_score(raw_score: float) -> float:
    """Normalize trend score to [0, 1]"""
    return max(0.0, min(1.0, raw_score))
