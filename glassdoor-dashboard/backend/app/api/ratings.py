"""Ratings dimension API endpoints."""

from fastapi import APIRouter, Query
from typing import Optional

from app.data_loader import load_ratings

router = APIRouter(tags=["ratings"])


@router.get("/ratings")
def get_ratings(run: Optional[str] = Query(None), company: Optional[str] = Query(None)):
    """Return detailed ratings, optionally filtered by company."""
    df = load_ratings(run)
    if df.empty:
        return []

    if company:
        df = df[df["company"] == company]

    result = []
    for _, row in df.iterrows():
        item = {}
        for col in df.columns:
            val = row[col]
            if isinstance(val, float):
                import math
                item[col] = None if math.isnan(val) else round(val, 2)
            else:
                item[col] = val
        result.append(item)

    return result
