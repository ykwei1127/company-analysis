# Changelog

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
