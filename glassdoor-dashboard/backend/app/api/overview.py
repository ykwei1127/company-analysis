"""Overview and location-based API endpoints."""

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional

from app.data_loader import (
    load_ratings, list_runs, delete_run, get_run_metadata, OUTPUT_DIR,
    CATEGORIES, load_ratings_by_category, calculate_region_weighted,
    normalize_company_name
)

router = APIRouter(tags=["overview"])


@router.get("/runs")
def get_runs():
    """List available scrape runs."""
    return list_runs()


@router.delete("/runs/{run_id}")
def remove_run(run_id: str):
    """Delete a scrape run and all its associated files."""
    return delete_run(run_id)


@router.get("/runs/{run_id}/download")
def download_run(run_id: str):
    """Download the XLSX file for a specific run."""
    if run_id == "latest":
        file_path = OUTPUT_DIR / "glassdoor_ratings.xlsx"
    else:
        file_path = OUTPUT_DIR / f"glassdoor_ratings_{run_id}.xlsx"

    if not file_path.exists():
        return {"error": "File not found"}

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


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
            "source_mode": _safe_str(row, "source_mode") or "unknown",
        }
        result.append(item)

    # Sort by overall descending
    result.sort(key=lambda x: x["overall"] or 0, reverse=True)
    for i, item in enumerate(result):
        item["rank"] = i + 1

    return result


@router.get("/overview/run-metadata")
def get_run_metadata_api(run: Optional[str] = Query(None)):
    """Return run metadata including source modes (city/country) and company list."""
    metadata = get_run_metadata(run)
    return {
        "match_modes": metadata.get("modes", []),
        "companies": metadata.get("companies", [])
    }


@router.get("/overview/by-location")
def get_overview_by_location(run: Optional[str] = Query(None)):
    """Return per-company per-location breakdown."""
    df = load_ratings(run)
    if df.empty:
        return []

    # Normalize company names so they match category definitions (same as export_static.py)
    if "company" in df.columns:
        df = df.copy()
        df["company"] = df["company"].apply(normalize_company_name)

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
            "source_mode": _safe_str(row, "source_mode") or "unknown",
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


# ═══════════════════════════════════════════════════════════════════
# Category-based API Endpoints
# ═══════════════════════════════════════════════════════════════════

@router.get("/categories")
def get_categories():
    """Return available categories with their metadata."""
    return {
        key: {
            'name': cat['name'],
            'companies': cat['companies'],
            'location_filter': cat['location_filter'],
            'weighted': cat['weighted']
        }
        for key, cat in CATEGORIES.items()
    }


@router.get("/overview/by-category")
def get_overview_by_category(
    category: str = Query(..., description="Category key: rd_taiwan, brand_global, oem_taiwan"),
    run: Optional[str] = Query(None)
):
    """
    Return overview data filtered by category.
    For brand_global, returns review-weighted scores per region.
    """
    df, category_companies = load_ratings_by_category(run, category)
    if df.empty:
        return {"companies": [], "regions": {}, "category": category}

    cat = CATEGORIES.get(category)
    if not cat:
        return {"companies": [], "regions": {}, "category": category}

    # Build company overview data
    companies_data = []
    dimensions = ['overall', 'culture', 'wlb', 'salary', 'career', 'diversity', 'management', 'recommend', 'ceo_approval']

    for company_name in category_companies:
        # Normalize for matching
        normalized_target = normalize_company_name(company_name)

        # Filter rows for this company
        company_rows = df[df['normalized_company'] == normalized_target]
        if company_rows.empty:
            continue

        # For Taiwan categories: aggregate by country=Taiwan or Global
        # For brand_global: use weighted calculation
        if cat['weighted']:
            # Use region-weighted calculation for brand_global
            region_scores = calculate_region_weighted(df, company_name, category)

            # Calculate overall weighted score across all regions
            all_reviews = sum(r.get('total_reviews', 0) for r in region_scores.values())
            if all_reviews > 0:
                company_data = {
                    'company': company_name,
                    'total_reviews': all_reviews,
                    'source_mode': 'weighted_region'
                }
                for dim in dimensions:
                    weighted_sum = sum(
                        r.get(dim, 0) * r.get('total_reviews', 0)
                        for r in region_scores.values()
                        if r.get(dim) is not None
                    )
                    dim_reviews = sum(
                        r.get('total_reviews', 0)
                        for r in region_scores.values()
                        if r.get(dim) is not None
                    )
                    company_data[dim] = round(weighted_sum / dim_reviews, 2) if dim_reviews > 0 else None

                company_data['regions'] = region_scores
                companies_data.append(company_data)
        else:
            # Simple aggregation for Taiwan categories
            # Aggregate by review-weighted average
            total_reviews = company_rows['total_reviews'].sum()
            if total_reviews == 0:
                continue

            company_data = {
                'company': company_name,
                'total_reviews': int(total_reviews),
                'source_mode': company_rows.iloc[0].get('source_mode', 'unknown') if len(company_rows) > 0 else 'unknown'
            }

            for dim in dimensions:
                valid_rows = company_rows[company_rows[dim].notna()]
                if not valid_rows.empty:
                    weighted_sum = (valid_rows[dim] * valid_rows['total_reviews']).sum()
                    dim_reviews = valid_rows['total_reviews'].sum()
                    company_data[dim] = round(weighted_sum / dim_reviews, 2) if dim_reviews > 0 else None
                else:
                    company_data[dim] = None

            companies_data.append(company_data)

    # Sort by overall rating
    companies_data.sort(key=lambda x: x.get('overall', 0) or 0, reverse=True)
    for i, item in enumerate(companies_data):
        item['rank'] = i + 1

    # Build region summary for brand_global
    region_summary = {}
    if cat['weighted']:
        for region_key in cat.get('regions', {}).keys():
            region_summary[region_key] = []
            for company_data in companies_data:
                if 'regions' in company_data and region_key in company_data['regions']:
                    region_data = company_data['regions'][region_key]
                    region_summary[region_key].append({
                        'company': company_data['company'],
                        'overall': region_data.get('overall'),
                        'total_reviews': region_data.get('total_reviews', 0)
                    })

    return {
        "category": category,
        "category_name": cat['name'],
        "companies": companies_data,
        "regions": region_summary if cat['weighted'] else None
    }


@router.get("/overview/regions")
def get_region_breakdown(
    company: str = Query(..., description="Company name"),
    category: str = Query(..., description="Category key (must be weighted category like brand_global)"),
    run: Optional[str] = Query(None)
):
    """Return region-weighted breakdown for a specific company."""
    df = load_ratings(run)
    if df.empty:
        return {"company": company, "regions": {}}

    region_scores = calculate_region_weighted(df, company, category)
    return {
        "company": company,
        "category": category,
        "regions": region_scores
    }
