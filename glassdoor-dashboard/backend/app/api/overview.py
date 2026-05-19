"""Overview and location-based API endpoints."""

from fastapi import APIRouter, Query
from typing import Optional

from app.data_loader import load_ratings, list_runs, delete_run

router = APIRouter(tags=["overview"])


@router.get("/runs")
def get_runs():
    """List available scrape runs."""
    return list_runs()


@router.delete("/runs/{run_id}")
def remove_run(run_id: str):
    """Delete a scrape run and all its associated files."""
    return delete_run(run_id)


@router.get("/overview")
def get_overview(run: Optional[str] = Query(None)):
    """Return per-company overview (Global rows only)."""
    df = load_ratings(run)
    if df.empty:
        return []

    # Filter to Global/company-level rows
    if "baseline_location" in df.columns:
        global_df = df[df["baseline_location"].str.lower().str.strip() == "global"]
        if global_df.empty:
            global_df = df
    else:
        global_df = df

    # Deduplicate by company (keep first)
    global_df = global_df.drop_duplicates(subset=["company"], keep="first")

    # Build response
    result = []
    for _, row in global_df.iterrows():
        item = {
            "company": _safe_str(row, "company"),
            "overall": _safe_float(row, "overall"),
            "culture": _safe_float(row, "culture"),
            "wlb": _safe_float(row, "wlb"),
            "salary": _safe_float(row, "salary"),
            "career": _safe_float(row, "career"),
            "diversity": _safe_float(row, "diversity"),
            "management": _safe_float(row, "management"),
            "recommend": _safe_float(row, "recommend"),
            "ceo_approval": _safe_float(row, "ceo_approval"),
            "total_reviews": _safe_int(row, "total_reviews"),
        }
        result.append(item)

    # Sort by overall descending
    result.sort(key=lambda x: x["overall"] or 0, reverse=True)
    for i, item in enumerate(result):
        item["rank"] = i + 1

    return result


@router.get("/overview/by-location")
def get_overview_by_location(run: Optional[str] = Query(None)):
    """Return per-company per-location breakdown."""
    df = load_ratings(run)
    if df.empty:
        return []

    result = []
    for _, row in df.iterrows():
        item = {
            "company": _safe_str(row, "company"),
            "baseline_location": _safe_str(row, "baseline_location") or "Global",
            "country": _safe_str(row, "country"),
            "overall": _safe_float(row, "overall"),
            "culture": _safe_float(row, "culture"),
            "wlb": _safe_float(row, "wlb"),
            "salary": _safe_float(row, "salary"),
            "career": _safe_float(row, "career"),
            "diversity": _safe_float(row, "diversity"),
            "management": _safe_float(row, "management"),
            "recommend": _safe_float(row, "recommend"),
            "ceo_approval": _safe_float(row, "ceo_approval"),
            "total_reviews": _safe_int(row, "total_reviews"),
        }
        result.append(item)

    return result


def _safe_float(row, col) -> Optional[float]:
    import math
    val = row.get(col)
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return None


def _safe_int(row, col) -> Optional[int]:
    import math
    val = row.get(col)
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_str(row, col) -> Optional[str]:
    import math
    val = row.get(col)
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    return str(val)
