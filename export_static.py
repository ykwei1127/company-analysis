#!/usr/bin/env python3
"""Export scraped data to static JSON for frontend static deployment (GitHub Pages)."""

import json
import math
import os
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"
STATIC_DIR = PROJECT_ROOT / "glassdoor-dashboard" / "frontend" / "public" / "static-data"

# Category definitions with companies and filters
CATEGORIES = {
    'rd_taiwan': {
        'name': 'R&D in Taiwan',
        'companies': ['ASUS', 'MSI', 'Trend Micro', 'Google', 'Acer'],
        'location_filter': 'Taiwan',
        'weighted': False,
        'regions': None
    },
    'brand_global': {
        'name': 'Global Brands',
        'companies': ['ASUS', 'Acer', 'Dell Technologies', 'HP Inc.', 'Lenovo', 'MSI', 'Trend Micro', 'NVIDIA', 'Google'],
        'location_filter': 'all',
        'weighted': True,
        'regions': {
            'north_america': ['United States', 'Canada'],
            'europe': ['United Kingdom', 'Germany', 'France', 'Netherlands', 'Italy', 'Spain', 'Hungary', 'Poland', 'Czech Republic', 'Sweden', 'Switzerland', 'Austria', 'Belgium', 'Denmark', 'Finland', 'Ireland', 'Norway', 'Portugal'],
            'asia': ['Taiwan', 'Japan', 'South Korea', 'India', 'Singapore', 'Thailand', 'Indonesia', 'Malaysia', 'China', 'United Arab Emirates'],
            'south_america': ['Brazil', 'Chile', 'Mexico'],
            'oceania': ['Australia', 'New Zealand'],
            'global': []
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

DIM_COLS = {
    "overall": "Overall",
    "culture": "Culture & Values",
    "wlb": "Work/Life Balance",
    "salary": "Compensation and Benefits",
    "career": "Career Opportunities",
    "diversity": "Diversity & Inclusion",
    "management": "Senior Management",
    "recommend": "Recommend",
    "ceo_approval": "CEO Approval",
}


def _safe_float(val):
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_str(val):
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    return str(val)


def _extract_company_name(raw: str) -> str:
    if not isinstance(raw, str):
        return str(raw)
    parts = raw.split(" - ")
    if len(parts) >= 2:
        return " - ".join(parts[:-1])
    return raw


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


def list_runs():
    runs = []
    if not OUTPUT_DIR.exists():
        return runs
    for f in OUTPUT_DIR.glob("glassdoor_ratings_*.csv"):
        m = re.search(r"(\d{8}_\d{4})", f.stem)
        if m:
            run_id = m.group(1)
            runs.append({"id": run_id, "label": run_id, "file": str(f)})
    default_file = OUTPUT_DIR / "glassdoor_ratings.csv"
    if default_file.exists():
        runs.append({"id": "latest", "label": "latest", "file": str(default_file)})
    runs.sort(key=lambda r: r["id"], reverse=True)
    return runs


def load_df(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    rename_map = {v: k for k, v in DIM_COLS.items()}
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
    if "company" in df.columns:
        df["company"] = df["company"].apply(_extract_company_name)
    pct_cols = ["recommend", "ceo_approval"]
    for col in pct_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace("%", "", regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "total_reviews" in df.columns:
        df["total_reviews"] = df["total_reviews"].astype(str).str.replace(",", "", regex=False).str.strip()
        df["total_reviews"] = pd.to_numeric(df["total_reviews"], errors="coerce")
    for col in DIM_COLS.keys():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def build_overview(df: pd.DataFrame) -> list:
    if df.empty:
        return []
    if "baseline_location" in df.columns:
        global_df = df[df["baseline_location"].str.lower().str.strip() == "global"]
        if global_df.empty:
            global_df = df
    else:
        global_df = df
    # Normalize company names before deduplication
    global_df = global_df.copy()
    global_df['normalized_company'] = global_df['company'].apply(normalize_company_name)
    global_df = global_df.drop_duplicates(subset=["normalized_company"], keep="first")
    result = []
    for _, row in global_df.iterrows():
        item = {
            "company": _safe_str(row.get("normalized_company")),
            "overall": _safe_float(row.get("overall")),
            "culture": _safe_float(row.get("culture")),
            "wlb": _safe_float(row.get("wlb")),
            "salary": _safe_float(row.get("salary")),
            "career": _safe_float(row.get("career")),
            "diversity": _safe_float(row.get("diversity")),
            "management": _safe_float(row.get("management")),
            "recommend": _safe_float(row.get("recommend")),
            "ceo_approval": _safe_float(row.get("ceo_approval")),
            "total_reviews": _safe_int(row.get("total_reviews")),
            "source_mode": _safe_str(row.get("source_mode")) or "unknown",
        }
        result.append(item)
    result.sort(key=lambda x: x["overall"] or 0, reverse=True)
    for i, item in enumerate(result):
        item["rank"] = i + 1
    return result


def build_by_location(df: pd.DataFrame) -> list:
    if df.empty:
        return []
    # Normalize company names for consistent matching
    df = df.copy()
    df['normalized_company'] = df['company'].apply(normalize_company_name)
    result = []
    for _, row in df.iterrows():
        item = {
            "company": _safe_str(row.get("normalized_company")),
            "baseline_location": _safe_str(row.get("baseline_location")) or "Global",
            "country": _safe_str(row.get("country")),
            "overall": _safe_float(row.get("overall")),
            "culture": _safe_float(row.get("culture")),
            "wlb": _safe_float(row.get("wlb")),
            "salary": _safe_float(row.get("salary")),
            "career": _safe_float(row.get("career")),
            "diversity": _safe_float(row.get("diversity")),
            "management": _safe_float(row.get("management")),
            "recommend": _safe_float(row.get("recommend")),
            "ceo_approval": _safe_float(row.get("ceo_approval")),
            "total_reviews": _safe_int(row.get("total_reviews")),
            "source_mode": _safe_str(row.get("source_mode")) or "unknown",
        }
        result.append(item)
    return result


def build_categories() -> dict:
    """Build categories metadata for frontend."""
    return {
        key: {
            'name': cat['name'],
            'companies': cat['companies'],
            'location_filter': cat['location_filter'],
            'weighted': cat['weighted']
        }
        for key, cat in CATEGORIES.items()
    }


def calculate_region_weighted(df: pd.DataFrame, company: str, category: str) -> dict:
    """Calculate review-weighted scores for each region."""
    cat = CATEGORIES.get(category)
    if not cat or not cat['weighted']:
        return {}
    
    regions = cat.get('regions', {})
    dimensions = list(DIM_COLS.keys())
    
    # Ensure normalized_company column exists
    if 'normalized_company' not in df.columns:
        df = df.copy()
        df['normalized_company'] = df['company'].apply(normalize_company_name)
    
    # Filter company data using normalized name
    target_normalized = normalize_company_name(company)
    company_df = df[df['normalized_company'] == target_normalized]
    if company_df.empty:
        return {}
    
    result = {}
    for region_key, countries in regions.items():
        if region_key == 'global':
            region_df = company_df[
                (company_df['baseline_location'].isna()) | 
                (company_df['baseline_location'].str.lower() == 'global')
            ]
        else:
            region_df = company_df[company_df['country'].isin(countries)]
        
        if region_df.empty:
            continue
            
        total_reviews = region_df['total_reviews'].sum()
        if total_reviews == 0:
            continue
            
        region_data = {'total_reviews': int(total_reviews)}
        for dim in dimensions:
            valid_rows = region_df[region_df[dim].notna()]
            if not valid_rows.empty:
                weighted_sum = (valid_rows[dim] * valid_rows['total_reviews']).sum()
                dim_reviews = valid_rows['total_reviews'].sum()
                region_data[dim] = round(weighted_sum / dim_reviews, 2) if dim_reviews > 0 else None
            else:
                region_data[dim] = None
        result[region_key] = region_data
    return result


def build_by_category(df: pd.DataFrame, category: str) -> dict:
    """Build category overview data matching backend API."""
    cat = CATEGORIES.get(category)
    if not cat:
        return {"companies": [], "regions": {}, "category": category}
    
    category_companies = cat['companies']
    dimensions = list(DIM_COLS.keys())
    
    # Normalize company names in df for matching
    df = df.copy()
    df['normalized_company'] = df['company'].apply(normalize_company_name)
    
    companies_data = []
    for company_name in category_companies:
        # Find rows for this company using normalized matching
        target_normalized = normalize_company_name(company_name)
        company_rows = df[df['normalized_company'] == target_normalized]
        
        # If no data found, still include company with null values
        if company_rows.empty:
            company_data = {
                'company': company_name,
                'total_reviews': 0,
                'source_mode': 'no_data'
            }
            for dim in dimensions:
                company_data[dim] = None
            if cat['weighted']:
                company_data['regions'] = {}
            companies_data.append(company_data)
            continue
            
        if cat['weighted']:
            # Use region-weighted calculation
            region_scores = calculate_region_weighted(df, company_name, category)
            all_reviews = sum(r.get('total_reviews', 0) for r in region_scores.values())
            if all_reviews == 0:
                # Still include company even with no reviews
                company_data = {
                    'company': company_name,
                    'total_reviews': 0,
                    'source_mode': 'weighted_region'
                }
                for dim in dimensions:
                    company_data[dim] = None
                company_data['regions'] = region_scores if region_scores else {}
                companies_data.append(company_data)
                continue
                
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
            # Filter to Taiwan data only
            if cat['location_filter'] == 'Taiwan':
                company_rows = company_rows[
                    (company_rows['country'] == 'Taiwan') |
                    (company_rows['baseline_location'].str.lower().isin(['taiwan', 'global']))
                ]
            
            # If no Taiwan data found, still include company with null values
            if company_rows.empty:
                company_data = {
                    'company': company_name,
                    'total_reviews': 0,
                    'source_mode': 'no_data'
                }
                for dim in dimensions:
                    company_data[dim] = None
                companies_data.append(company_data)
                continue
                
            total_reviews = company_rows['total_reviews'].sum()
            if total_reviews == 0:
                # Still include company even with no reviews
                company_data = {
                    'company': company_name,
                    'total_reviews': 0,
                    'source_mode': company_rows.iloc[0].get('source_mode', 'unknown') if len(company_rows) > 0 else 'unknown'
                }
                for dim in dimensions:
                    company_data[dim] = None
                companies_data.append(company_data)
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
    
    # Sort by overall rating (null values go to the end)
    companies_data.sort(key=lambda x: (x.get('overall') is None, x.get('overall', 0) or 0), reverse=False)
    companies_data.reverse()
    for i, item in enumerate(companies_data):
        item['rank'] = i + 1
    
    # Build region summary for weighted categories (like brand_global)
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


def build_metadata(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"match_modes": [], "companies": []}
    modes = set()
    companies = []

    def _normalize_mode(m):
        return "office" if m == "baseline" else m

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
        "match_modes": sorted(list(modes)),
        "companies": companies,
    }


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {path.relative_to(STATIC_DIR.parent.parent.parent)}")


def export_run(run_id: str, csv_path: str, out_dir: Path):
    df = load_df(csv_path)
    write_json(out_dir / "overview.json", build_overview(df))
    write_json(out_dir / "by-location.json", build_by_location(df))
    write_json(out_dir / "metadata.json", build_metadata(df))
    
    # Export by-category data for each category
    for category in CATEGORIES.keys():
        write_json(out_dir / f"by-category-{category}.json", build_by_category(df, category))


def main():
    print("🔄 Exporting static data...")
    print(f"   Source: {OUTPUT_DIR}")
    print(f"   Target: {STATIC_DIR}")

    runs = list_runs()
    if not runs:
        print("❌ No CSV files found in output/. Run the scraper first.")
        sys.exit(1)

    # Clear and recreate static-data dir
    if STATIC_DIR.exists():
        shutil.rmtree(STATIC_DIR)
    STATIC_DIR.mkdir(parents=True)

    # Export each run
    for run in runs:
        run_id = run["id"]
        print(f"\n📁 Exporting run: {run_id}")
        export_run(run_id, run["file"], STATIC_DIR / run_id)

    # Export a 'latest' copy of the newest non-'latest' run
    non_latest = [r for r in runs if r["id"] != "latest"]
    if non_latest:
        newest = non_latest[0]
        print(f"\n📁 Exporting 'latest' (copy of {newest['id']})")
        export_run("latest", newest["file"], STATIC_DIR / "latest")
    elif runs:
        print(f"\n📁 Exporting 'latest'")
        export_run("latest", runs[0]["file"], STATIC_DIR / "latest")

    # Write categories.json (for frontend category selector)
    write_json(STATIC_DIR / "categories.json", build_categories())
    print(f"  ✓ categories.json")

    # Write runs.json (exclude the auto-generated 'latest' entry to avoid confusion)
    runs_list = [{"id": r["id"], "label": r["label"]} for r in runs if r["id"] != "latest"]
    if not runs_list and runs:
        runs_list = [{"id": r["id"], "label": r["label"]} for r in runs]
    write_json(STATIC_DIR / "runs.json", runs_list)

    # Copy data/ folder for URL verification in Settings page
    DATA_DIR = PROJECT_ROOT / "data"
    STATIC_DATA_DIR = STATIC_DIR / "data"
    if DATA_DIR.exists():
        if STATIC_DATA_DIR.exists():
            shutil.rmtree(STATIC_DATA_DIR)
        shutil.copytree(DATA_DIR, STATIC_DATA_DIR)
        
        # Create index.json for the Settings page to list available files
        data_files = []
        for json_file in sorted(DATA_DIR.glob("*.json")):
            # Parse filename to extract company name and mode
            # Expected format: {company}_{mode}.json or {company}-{location}.json
            stem = json_file.stem
            parts = stem.rsplit('_', 1)
            if len(parts) == 2:
                name, mode = parts
            else:
                name = stem
                mode = "unknown"
            
            # Try to normalize company name
            normalized_name = normalize_company_name(name.replace('-', ' '))
            
            # Count entries in the file
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    # If content is a list, count items; if dict with 'locations', count that
                    if isinstance(content, list):
                        entries = len(content)
                    elif isinstance(content, dict) and 'locations' in content:
                        entries = len(content['locations'])
                    else:
                        entries = 0
            except Exception:
                entries = 0
            
            data_files.append({
                "name": normalized_name,
                "file": json_file.name,
                "mode": mode,
                "entries": entries
            })
        
        write_json(STATIC_DATA_DIR / "index.json", {"companies": data_files})
        print(f"  ✓ Copied data/ folder ({len(list(DATA_DIR.glob('*.json')))} files + index.json)")

    print(f"\n✅ Export complete! {len(runs_list)} run(s) exported.")
    print(f"   Next: cd glassdoor-dashboard/frontend && npm run build:static")


if __name__ == "__main__":
    main()
