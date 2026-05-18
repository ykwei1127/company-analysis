# Changelog

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
