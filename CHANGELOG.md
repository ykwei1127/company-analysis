# Changelog

## 2026-05-20 (Session 2)

### Added
- **City Match mode** (`company_finder.py city`) — 第 4 種 URL 清單類型，以 ASUS 辦公室城市為基準，搜尋其他公司在同一城市的 Review URL，輸出 `*_city.json`
- **GitHub Pages 靜態部署** — `export_static.py` 將 output/ 匯出為靜態 JSON，`npm run deploy` 部署至 GitHub Pages
  - 靜態網站：https://ykwei1127.github.io/company-analysis/
  - Demo Mode：Scraper / Settings 頁面可瀏覽但控制項停用，顯示「Demo Mode — Read Only」提示
  - `.nojekyll` + `gh-pages --dotfiles` 解決 Jekyll 過濾 `_` 開頭 asset 問題
- **爬蟲完成後自動刷新 run 選單** — `ScraperPage.vue` 偵測到爬蟲停止後，自動呼叫 `fetchRuns()` 並切換到最新 run

### Fixed
- **ASUS OVERALL / RANK KPI 顯示 `—`** — CSV 儲存的公司名為 `"Asus"`，前端 hardcode `'ASUS'` 導致比對失敗；改用 `.toLowerCase()` 比對 + `getCompanyColor()` case-insensitive helper
- **雷達圖顏色全灰** — `COMPANY_COLORS['Asus']` 因大小寫找不到回傳 `'#555'`；`getCompanyColor()` 現在 fallback 到 palette 顏色
- **Comparison 頁面初始不選任何公司** — `DEFAULT_SELECTED = ['ASUS']` 從不匹配；改為 `loadData()` 完成後動態初始化 `selectedCompanies`
- **Scraper `--source-mode office` 無效** — `office` 不在 `glassdoor_scraper_unified.py` 的 choices 列表；已補上
- **office 模式 `KeyError: 'company'`** — `parallel_scrape` 嘗試讀取 `_e['company']` 但 office 模式 entry 格式不同；修正為使用正確欄位
- **office 模式跑了兩次 ASUS** — baseline 邏輯重複加入已在 office 清單中的 ASUS；加入 dedup 判斷

### Changed
- **Settings 頁面** — 新增 City Match 模式卡片，Build URL Lists 現在有 4 張卡（Office / Country / City / Scan）
- **Scraper 頁面 List Type 下拉選單** — 新增 `City Match` 選項
- **`vite.config.ts`** — 改為 factory function，static mode 使用 `/company-analysis/` base path，dev 用 `/`
- **`api/index.ts`** — `STATIC_MODE` 開關：靜態模式讀取 JSON 檔案，scraper/settings API 回傳 noop
- **`main.ts`** — Router 改用 `createWebHistory(import.meta.env.BASE_URL)` 支援 GitHub Pages 子路徑


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
  - Added CSS overrides in `App.vue` for el-alert, el-collapse, el-checkbox, el-form, el-popover, el-select-dropdown

### Added
- `migrate_filenames.py` — one-time script to rename old data files to new naming convention
- Full step-by-step tutorial in `glassdoor-dashboard/README.md` (Phase 1: URL lists → Phase 2: Scraper → Phase 3: View results)


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
