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
    global_df = global_df.drop_duplicates(subset=["company"], keep="first")
    result = []
    for _, row in global_df.iterrows():
        item = {
            "company": _safe_str(row.get("company")),
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
    result = []
    for _, row in df.iterrows():
        item = {
            "company": _safe_str(row.get("company")),
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

    # Write runs.json (exclude the auto-generated 'latest' entry to avoid confusion)
    runs_list = [{"id": r["id"], "label": r["label"]} for r in runs if r["id"] != "latest"]
    if not runs_list and runs:
        runs_list = [{"id": r["id"], "label": r["label"]} for r in runs]
    write_json(STATIC_DIR / "runs.json", runs_list)

    print(f"\n✅ Export complete! {len(runs_list)} run(s) exported.")
    print(f"   Next: cd glassdoor-dashboard/frontend && npm run build:static")


if __name__ == "__main__":
    main()
