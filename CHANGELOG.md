# Changelog

# Changelog

## 2026-05-20
### Changed (Breaking Refactor)
- **Unified workflow terminology**: replaced confusing `baseline/explore/match/city` with three clear **URL list types**
  - `office` (was: explore/baseline/city) → `*_office.json`
  - `country` (was: match country) → `*_country.json`
  - `scan` (unchanged) → `*_scan.json`
- **`company_finder.py`**: `run_explore()` → `run_office()`, `run_match()` → `run_country()`, updated `__main__` dispatch
- **Settings page**: replaced 3-step flow with card-based UI (Office / Country / Scan), added "View URL Lists" tab
- **Scraper page**: replaced "Data Source + Match Mode" dual dropdowns with single "List Type" dropdown
- **Overview page**: "Match Modes" → "List Types", mixed-mode warning updated, Run Info Banner replaced with low-profile `.run-info-bar`
- **Backend API**: new endpoints `/finder/office`, `/finder/country`; `list_companies()` reads `*_office.json`/`*_country.json`/`*_scan.json`; `get_baseline()` accepts `?file=` param
- **`glassdoor_scraper_unified.py`**: glob pattern updated, source_mode detection updated, `Source Mode = 'baseline'` → `'office'`
- **`data_loader.py`**: `_normalize_mode()` maps `baseline`/`city` → `office`
- **`data/asus_locations.json`** renamed to **`data/asus_office.json`** (run `migrate_filenames.py`)

### Fixed
- **Dark mode**: Element Plus components (el-alert, el-collapse, el-checkbox, el-popover, etc.) now correctly use dark theme
  - Root cause: `theme.ts` only set `data-theme="dark"` attribute; Element Plus requires `.dark` class on `<html>`
  - Fix: theme store now adds/removes `.dark` class alongside `data-theme` attribute

### Added
- `migrate_filenames.py` — one-time script to rename old data files to new naming convention

## 2026-05-19
### Added
- **Settings & Companies page** (Dashboard)
  - Tab-based UI: Companies, Baseline Locations, Scraper Config
  - Add/remove companies to `COMPANIES_TO_MATCH` dynamically from UI
  - Run Match / Explore from dashboard with live log streaming
  - Matched companies table with remove button
  - ASUS baseline locations table
- **Delete run** button next to run selector (removes CSV, XLSX, and all log files)
- LAN access: Vite and uvicorn now bind to `0.0.0.0`

### Fixed
- Cloudflare false positive detection: removed generic 'just a moment' from body check, now only checks page title
- Added smart wait (up to 5s) after page load for Cloudflare JS challenge auto-pass instead of fixed 3s sleep
- Dark theme overrides for `el-tabs` component

## 2026-05-18
### Added
- **Web Dashboard** (`glassdoor-dashboard/`)
  - Backend: FastAPI with overview, ratings, and scraper control APIs
  - Frontend: Vue 3 + Element Plus + ECharts dark theme dashboard
  - Pages: Overview, Comparison (radar chart), Locations (heatmap), Scraper control
  - Scrape run selector to switch between different data snapshots
  - CEO Approval column in Overview and Location detail tables
  - Chrome debug port status check and Glassdoor login verification
- Simplified progress output with `[PROGRESS]` tags for dashboard parsing
- English log messages for international compatibility

### Changed
- Replaced tqdm progress bar with simple text output (3s interval)
- Scraper parallel loop sleep increased to 3s to reduce overhead

## 2026-05-11
### Added
- Parallel scraping across multiple Chrome debug ports
- CSV output format with all rating dimensions
- Per-port log files and run-level logging
- Review URL column in output
- CEO Approval column in scraper output
- 15 companies matched data files

### Fixed
- Company search bug with empty text results
- Immediate log flush for real-time monitoring
