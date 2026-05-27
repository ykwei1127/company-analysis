"""Load scraped Glassdoor CSV data for the dashboard API."""

import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd

# Resolve project root (two levels up from this file -> company-analysis/)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"


def list_runs() -> list[dict]:
    """Return available scrape runs sorted newest-first."""
    runs = []
    if not OUTPUT_DIR.exists():
        return runs
    for f in OUTPUT_DIR.glob("glassdoor_ratings_*.csv"):
        # Expected pattern: glassdoor_ratings_YYYYMMDD_HHMM.csv
        m = re.search(r"(\d{8}_\d{4})", f.stem)
        if m:
            run_id = m.group(1)
            runs.append({"id": run_id, "file": str(f), "label": run_id})
    # Also check for the default file (no timestamp)
    default_file = OUTPUT_DIR / "glassdoor_ratings.csv"
    if default_file.exists():
        runs.append({"id": "latest", "file": str(default_file), "label": "latest"})
    runs.sort(key=lambda r: r["id"], reverse=True)
    return runs


def delete_run(run_id: str) -> dict:
    """Delete all files associated with a run (CSV, XLSX, logs)."""
    deleted = []
    if run_id == "latest":
        # Delete the default files
        for ext in ["csv", "xlsx"]:
            f = OUTPUT_DIR / f"glassdoor_ratings.{ext}"
            if f.exists():
                f.unlink()
                deleted.append(f.name)
    else:
        # Delete timestamped output files
        for ext in ["csv", "xlsx"]:
            f = OUTPUT_DIR / f"glassdoor_ratings_{run_id}.{ext}"
            if f.exists():
                f.unlink()
                deleted.append(f.name)
        # Delete associated log files
        if LOGS_DIR.exists():
            for f in LOGS_DIR.glob(f"run_{run_id}*"):
                f.unlink()
                deleted.append(f.name)
    return {"deleted": deleted, "count": len(deleted)}


def _find_csv(run_id: Optional[str] = None) -> Optional[Path]:
    """Find the CSV file for a given run_id, or the latest."""
    if run_id and run_id != "latest":
        target = OUTPUT_DIR / f"glassdoor_ratings_{run_id}.csv"
        if target.exists():
            return target
    # Fallback: default file
    default = OUTPUT_DIR / "glassdoor_ratings.csv"
    if default.exists():
        return default
    # Last resort: newest timestamped file
    files = sorted(OUTPUT_DIR.glob("glassdoor_ratings_*.csv"), reverse=True)
    return files[0] if files else None


# Column mapping: CSV header -> API field name
DIM_COLS = {
    "overall": "Overall",
    "culture": "Culture & Values",
    "wlb": "Work/Life Balance",
    "salary": "Compensation and Benefits",
    "career": "Career Opportunities",
    "diversity": "Diversity & Inclusion",
    "management": "Senior Management",
    "ceo_approval": "CEO Approval",
}


def load_ratings(run_id: Optional[str] = None) -> pd.DataFrame:
    """Load and normalize the ratings CSV."""
    csv_path = _find_csv(run_id)
    if csv_path is None:
        return pd.DataFrame()

    df = pd.read_csv(csv_path)

    # Normalize column names
    rename_map = {v: k for k, v in DIM_COLS.items()}
    # Also handle common alternative names
    rename_map.update({
        "Company": "company",
        "Baseline Location": "baseline_location",
        "Country": "country",
        "Recommend": "recommend",
        "Recommend to a Friend": "recommend",
        "Total Reviews": "total_reviews",
        "Review URL": "review_url",
        "Source Mode": "source_mode",
    })
    df = df.rename(columns=rename_map)

    # Parse company name: CSV may have "Dell Technologies - Global" format
    if "company" in df.columns:
        # Extract pure company name by removing " - Location" suffix
        df["company"] = df["company"].apply(_extract_company_name)

    # Clean percentage and comma formatting before numeric conversion
    pct_cols = ["recommend", "ceo_approval"]
    for col in pct_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace("%", "", regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "total_reviews" in df.columns:
        df["total_reviews"] = df["total_reviews"].astype(str).str.replace(",", "", regex=False).str.strip()
        df["total_reviews"] = pd.to_numeric(df["total_reviews"], errors="coerce")

    # Ensure other numeric columns
    numeric_cols = list(DIM_COLS.keys())
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def get_run_metadata(run_id: Optional[str] = None) -> dict:
    """Get metadata about a run including source modes from the CSV."""
    df = load_ratings(run_id)
    if df.empty:
        return {"modes": [], "companies": []}

    modes = set()
    companies = []

    def _normalize_mode(m: str) -> str:
        # 'baseline' is a legacy name — treat as 'office' for grouping
        return 'office' if m == 'baseline' else m

    if "source_mode" in df.columns and "company" in df.columns:
        for company, grp in df.groupby("company"):
            raw_mode = grp["source_mode"].dropna().iloc[0] if not grp["source_mode"].dropna().empty else "unknown"
            mode = _normalize_mode(raw_mode)
            modes.add(mode)
            companies.append({"name": company, "mode": mode})
    elif "company" in df.columns:
        for company in df["company"].unique():
            companies.append({"name": company, "mode": "unknown"})

    return {
        "modes": sorted(list(modes)),
        "companies": companies,
    }


def _extract_company_name(raw: str) -> str:
    """Extract company name from 'Company - Location' format."""
    if not isinstance(raw, str):
        return str(raw)
    # Split on " - " and take everything before the last " - "
    # Handle cases like "Dell Technologies - Fremont, CA"
    parts = raw.split(" - ")
    if len(parts) >= 2:
        return " - ".join(parts[:-1])
    return raw


# ═══════════════════════════════════════════════════════════════════
# Category Definitions & Region Weighted Calculation
# ═══════════════════════════════════════════════════════════════════

# Category definitions with companies and filters
CATEGORIES = {
    'rd_taiwan': {
        'name': 'R&D in Taiwan',
        'companies': ['ASUS', 'MSI', 'Trend Micro', 'Google', 'Acer'],
        'location_filter': 'Taiwan',  # Filter to Taiwan reviews only
        'weighted': False,
        'regions': None
    },
    'brand_global': {
        'name': 'Global Brands',
        'companies': ['ASUS', 'Acer', 'Dell Technologies', 'HP Inc.', 'Lenovo', 'MSI', 'Trend Micro', 'NVIDIA', 'Google'],
        'location_filter': 'all',  # All locations
        'weighted': True,  # Use review-weighted regional calculation
        'regions': {
            'north_america': ['United States', 'Canada'],
            'europe': ['United Kingdom', 'Germany', 'France', 'Netherlands', 'Italy', 'Spain', 'Hungary', 'Poland', 'Czech Republic', 'Sweden', 'Switzerland', 'Austria', 'Belgium', 'Denmark', 'Finland', 'Ireland', 'Norway', 'Portugal'],
            'asia': ['Taiwan', 'Japan', 'South Korea', 'India', 'Singapore', 'Thailand', 'Indonesia', 'Malaysia', 'China', 'United Arab Emirates'],
            'south_america': ['Brazil', 'Chile', 'Mexico'],
            'oceania': ['Australia', 'New Zealand'],
            'global': []  # Special: global level reviews
        }
    },
    'oem_taiwan': {
        'name': 'Taiwan Tech OEMs',
        'companies': ['ASUS', 'Quanta Computer', 'Wistron', 'Compal Electronics', 'Wiwynn', 'TSMC', 'Delta Electronics', 'Inventec', 'Pegatron', 'AU Optronics'],
        'location_filter': 'Taiwan',
        'weighted': False,
        'regions': None
    }
}


def get_category_companies(category: str) -> list[str]:
    """Get list of companies for a category."""
    cat = CATEGORIES.get(category)
    if not cat:
        return []
    return cat['companies']


def normalize_company_name(name: str) -> str:
    """Normalize company name for matching (case-insensitive, handle variations)."""
    name_lower = name.lower().strip()
    # Handle common variations
    if 'trend' in name_lower and 'micro' in name_lower:
        return 'Trend Micro'
    if name_lower == 'trend micro inc.':
        return 'Trend Micro'
    if name_lower in ['acer', 'acer group']:
        return 'Acer'
    if name_lower in ['dell', 'dell technologies']:
        return 'Dell Technologies'
    if name_lower == 'hp' or name_lower == 'hp inc.':
        return 'HP Inc.'
    if name_lower == 'google':
        return 'Google'
    if name_lower == 'nvidia':
        return 'NVIDIA'
    if name_lower == 'lenovo':
        return 'Lenovo'
    if name_lower in ['asus', 'asustek']:
        return 'ASUS'
    if name_lower == 'msi' or name_lower == 'micro-star international':
        return 'MSI'
    if name_lower == 'quanta' or name_lower == 'quanta computer':
        return 'Quanta Computer'
    if name_lower == 'wistron':
        return 'Wistron'
    if name_lower in ['compal', 'compal electronics']:
        return 'Compal Electronics'
    if name_lower == 'wiwynn':
        return 'Wiwynn'
    if name_lower in ['tsmc', 'taiwan semiconductor']:
        return 'TSMC'
    if name_lower in ['delta', 'delta electronics']:
        return 'Delta Electronics'
    if name_lower == 'inventec':
        return 'Inventec'
    if name_lower == 'pegatron':
        return 'Pegatron'
    if name_lower in ['auo', 'au optronics']:
        return 'AU Optronics'
    return name.strip()


def match_company_to_category(company_name: str, category_companies: list[str]) -> bool:
    """Check if a company matches any company in the category list (case-insensitive)."""
    normalized_input = normalize_company_name(company_name)
    normalized_category = [normalize_company_name(c) for c in category_companies]
    return normalized_input in normalized_category


def calculate_region_weighted(df: pd.DataFrame, company: str, category: str) -> dict:
    """
    Calculate review-weighted scores for each region.
    Returns: {region_key: {dimension: weighted_score, total_reviews: count}}
    """
    cat = CATEGORIES.get(category)
    if not cat or not cat['weighted']:
        return {}
    
    regions = cat.get('regions', {})
    result = {}
    
    # Filter to this company
    company_df = df[df['company'].apply(lambda x: match_company_to_category(x, [company]))]
    if company_df.empty:
        return {}
    
    dimensions = ['overall', 'culture', 'wlb', 'salary', 'career', 'diversity', 'management', 'recommend', 'ceo_approval']
    
    for region_key, countries in regions.items():
        if region_key == 'global':
            # Global level: rows where baseline_location is Global or empty
            region_df = company_df[
                (company_df['baseline_location'].isna()) | 
                (company_df['baseline_location'].str.lower() == 'global')
            ]
        else:
            # Region: filter by country list
            region_df = company_df[company_df['country'].isin(countries)]
        
        if region_df.empty:
            continue
        
        # Calculate review-weighted average for each dimension
        region_data = {'total_reviews': 0}
        total_weight = region_df['total_reviews'].sum()
        
        if total_weight > 0:
            region_data['total_reviews'] = int(total_weight)
            for dim in dimensions:
                if dim in region_df.columns:
                    # Weighted average: sum(value * reviews) / sum(reviews)
                    valid_rows = region_df[region_df[dim].notna()]
                    if not valid_rows.empty:
                        weighted_sum = (valid_rows[dim] * valid_rows['total_reviews']).sum()
                        region_data[dim] = weighted_sum / valid_rows['total_reviews'].sum()
                    else:
                        region_data[dim] = None
        
        if region_data['total_reviews'] > 0:
            result[region_key] = region_data
    
    return result


def load_ratings_by_category(run_id: Optional[str] = None, category: Optional[str] = None) -> tuple[pd.DataFrame, list]:
    """
    Load ratings filtered by category.
    Returns: (filtered_df, category_companies)
    """
    df = load_ratings(run_id)
    if df.empty or not category:
        return df, []
    
    cat = CATEGORIES.get(category)
    if not cat:
        return df, []
    
    # Filter by category companies
    category_companies = cat['companies']
    df['normalized_company'] = df['company'].apply(normalize_company_name)
    normalized_targets = [normalize_company_name(c) for c in category_companies]
    
    mask = df['normalized_company'].isin(normalized_targets)
    filtered_df = df[mask].copy()
    
    # Apply location filter
    if cat['location_filter'] == 'Taiwan':
        # Keep only Taiwan rows or Global
        location_mask = (
            (filtered_df['country'] == 'Taiwan') | 
            (filtered_df['baseline_location'].str.lower() == 'global') |
            (filtered_df['baseline_location'].str.lower() == 'taiwan')
        )
        filtered_df = filtered_df[location_mask]
    
    return filtered_df, category_companies
