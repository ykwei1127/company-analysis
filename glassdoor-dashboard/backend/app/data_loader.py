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
