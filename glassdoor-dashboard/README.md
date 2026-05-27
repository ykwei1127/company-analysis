# Glassdoor Dashboard

Vue 3 + FastAPI 互動式 Dashboard，用於檢視爬取的 Glassdoor 評分數據、建立 URL 清單、控制爬蟲。支援本機完整操作模式，以及靜態唯讀的 GitHub Pages Demo 模式。

## 啟動

```powershell
.\start.ps1
```

會同時啟動：
- **Backend** — FastAPI on http://localhost:8000 (uvicorn --reload)
- **Frontend** — Vite dev server on http://localhost:5173

預設 bind `0.0.0.0`，區域網路可用 `http://<IP>:5173` 連入。

---

## 從零開始完整操作流程

### 前置：啟動環境

1. 執行 `啟動Chrome.bat`（port 9222），在開啟的 Chrome 中登入 Glassdoor
2. 執行 `.\start.ps1` 啟動 Dashboard，打開 http://localhost:5173

---

### Phase 1：建立 URL 清單（只需做一次）

進入 **Settings** 頁面：

**Step 1 — 確認公司列表**
- **Companies** 區塊顯示目前 `COMPANIES_TO_MATCH` 的公司
- 輸入框可新增公司名稱 → **Add**（ID/URL 自動搜尋）
- 勾選想要的公司

**Step 2 — 建立清單**

| 目標 | 按鈕 | 輸出檔案 | 備注 |
|------|------|---------|------|
| 各公司辦公室城市評分 | **Build Office List** | `data/*_office.json` | 各公司自身辦公室地點 |
| 各國國家級評分（推薦） | **Build Country List** | `data/*_country.json` | 需先有 `asus_office.json` |
| 以 ASUS 城市基準比對 | **Build City List** | `data/*_city.json` | 需先有 `asus_office.json` |
| 掃描全球哪些國家有評論 | **Build Scan List** | `data/*_scan.json` | — |

點下去後右上角狀態列會顯示進度 log，等完成為止。

**Step 3 — 確認結果**
- 切到 **View URL Lists** tab → 選剛建好的檔案 → 確認各地區 status 為 `found`

---

### Phase 2：抓取評分內容（定期執行）

進入 **Scraper** 頁面：

1. **Chrome Ports** 確認 9222 綠燈 ✅
2. **List Type** 選剛建的類型（如 `Country`）
3. **Companies** 選要抓的公司（留空 = 全部）
4. 按 **Start Scraper**，等 log 顯示完成
5. 完成後右上角 run 選單自動切換到最新結果
6. 輸出：`output/glassdoor_ratings_YYYYMMDD_HHMM.xlsx`

> **平行加速**：同時開 `啟動Chrome_9223.bat`、`啟動Chrome_9224.bat`，在 Ports 勾選 9222 + 9223 + 9224，速度提升約 3x

---

### Phase 3：查看結果

| 頁面 | 看什麼 |
|------|--------|
| **Overview** | 各公司 Global / Taiwan 評分 KPI，各維度長條圖比較，頂部 run 下拉切換不同次結果 |
| **Comparison** | 選公司 + 地區 → 雷達圖比較各維度 |
| **Locations** | 地區熱力圖，哪個城市哪家公司分高 |

---

## 頁面說明

| 頁面 | 功能 |
|------|------|
| **Overview** | 三個類別（R&D in Taiwan、Global Brands、Taiwan Tech OEMs）評分比較，頂部顯示 Source Mode 標籤（office/city/country/scan） |
| **Comparison** | 雷達圖多維度比較，支援三個類別切換，ASUS 固定顯示在 legend 首位，預設選取 ASUS + 前 2 名公司 |
| **Locations** | 地區評分熱力圖，Taiwan-only 顯示單一 Taiwan 資料，Global Brands 顯示區域加權計算 tooltip |
| **Scraper** | Chrome 狀態管理、啟動/停止爬蟲、List Type 篩選、公司選擇、即時 Log |
| **Settings** | 建立 URL 清單（Office/Country/City/Scan）、公司管理、URL List 顯示 Source 欄位、Scraper Config |

### Source Mode 標籤顏色對照

- 🔴 **city**（紅色）- 城市級別匹配
- 🟢 **country**（綠色）- 國家級別
- 🟠 **office**（橙色）- 辦公室地點
- 🔵 **scan**（藍色）- 全球掃描
- ⚪ **Demo**（灰色）- 靜態模式（GitHub Pages）
- 🟣 **Mixed**（紫色）- 混合模式（多種來源）

---

## 靜態部署（GitHub Pages Demo）

供無法啟動本機後端的使用者唯讀瀏覽。

```powershell
# 在專案根目錄執行
.\venv\Scripts\python.exe export_static.py   # 匯出最新資料為靜態 JSON

cd frontend
npm run deploy                               # 建置並推送至 gh-pages branch
```

靜態網站：**https://ykwei1127.github.io/company-analysis/**

**Demo Mode 特性：**
- Overview、Comparison、Locations 正常顯示資料
- Scraper / Settings 頁面可瀏覽，但所有控制項停用並顯示「Demo Mode — Read Only」提示
- 不需要後端、Chrome 或 Glassdoor 帳號

---

## 目錄結構

```
glassdoor-dashboard/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI app entry
│       ├── data_loader.py   # CSV/run 讀取邏輯（含 source_mode 正規化）
│       └── api/
│           ├── overview.py  # 評分資料 API
│           ├── ratings.py   # 詳細評分 API
│           ├── scraper.py   # 爬蟲控制 API
│           └── settings.py  # 公司管理、URL 清單建立、Finder 控制 API
├── frontend/
│   └── src/
│       ├── views/           # 頁面元件（Overview/Comparison/Locations/Scraper/Settings）
│       ├── stores/          # Pinia stores（finder store 管理全域任務狀態）
│       ├── api/             # API layer（含 STATIC_MODE 切換）
│       └── App.vue          # 主框架（sidebar + router + 全域狀態列）
├── frontend/.env.static     # VITE_STATIC_MODE=true，靜態建置用
└── start.ps1                # 一鍵啟動腳本
```

## 後端 API 重點

| 路徑 | 說明 |
|------|------|
| `POST /settings/finder/office` | 建立 Office URL 清單（對應 `company_finder.py office`） |
| `POST /settings/finder/country` | 建立 Country URL 清單 |
| `POST /settings/finder/city` | 建立 City Match URL 清單 |
| `POST /settings/finder/scan` | 建立 World Scan 清單 |
| `GET /settings/finder/status` | 查詢目前 Finder 執行狀態與 log |
| `GET /settings/companies` | 列出所有 URL 清單檔案（office/country/city/scan） |
| `GET /settings/baseline?file=xxx` | 查看某個 URL 清單的內容 |
| `POST /scraper/start` | 啟動爬蟲（支援 `source_mode=office/country/city/scan/all`） |

## 技術棧

- **Frontend**: Vue 3, Element Plus, ECharts, Pinia, TypeScript
- **Backend**: FastAPI, Pandas, uvicorn
- **Theme**: Dark/Light 可切換（Element Plus `.dark` class + CSS variables）
- **Static Deploy**: Vite static build + gh-pages


## 啟動

```powershell
.\start.ps1
```

會同時啟動：
- **Backend** — FastAPI on http://localhost:8000 (uvicorn --reload)
- **Frontend** — Vite dev server on http://localhost:5173

預設 bind `0.0.0.0`，區域網路可用 `http://<IP>:5173` 連入。

---

## 從零開始完整操作流程

### 前置：啟動環境

1. 執行 `啟動Chrome.bat`（port 9222），在開啟的 Chrome 中登入 Glassdoor
2. 執行 `.\start.ps1` 啟動 Dashboard，打開 http://localhost:5173

---

### Phase 1：建立 URL 清單（只需做一次）

進入 **Settings** 頁面：

**Step 1 — 確認公司列表**
- **Companies** 區塊顯示目前 `COMPANIES_TO_MATCH` 的公司
- 輸入框可新增公司名稱 → **Add**（ID/URL 自動搜尋）
- 勾選想要的公司

**Step 2 — 建立清單**

| 目標 | 按鈕 | 輸出檔案 |
|------|------|---------|
| 各公司辦公室城市評分 | **Build Office List** | `data/*_office.json` |
| 各國國家級評分（推薦） | **Build Country List** | `data/*_country.json` |
| 掃描全球哪些國家有評論 | **Build Scan List** | `data/*_scan.json` |

點下去後右上角狀態列會顯示進度 log，等完成為止。

**Step 3 — 確認結果**
- 切到 **View URL Lists** tab → 選剛建好的檔案 → 確認各地區 status 為 `found`

---

### Phase 2：抓取評分內容（定期執行）

進入 **Scraper** 頁面：

1. **Chrome Ports** 確認 9222 綠燈 ✅
2. **List Type** 選剛建的類型（如 `Country`）
3. **Companies** 選要抓的公司（留空 = 全部）
4. 按 **Start Scraper**，等 log 顯示完成
5. 輸出：`output/glassdoor_ratings_YYYYMMDD_HHMM.xlsx`

> **平行加速**：同時開 `啟動Chrome_9223.bat`、`啟動Chrome_9224.bat`，在 Ports 勾選 9222 + 9223 + 9224，速度提升約 3x

---

### Phase 3：查看結果

| 頁面 | 看什麼 |
|------|--------|
| **Overview** | 三個類別（R&D in Taiwan、Global Brands、Taiwan Tech OEMs）評分排名與比較 |
| **Comparison** | 雷達圖多維度比較，支援類別切換，預設 ASUS + 前 2 名 |
| **Locations** | 地區熱力圖，Taiwan-only 與 Global Brands 加權計算 |

---

## 頁面說明

| 頁面 | 功能 |
|------|------|
| **Overview** | 三個類別（R&D in Taiwan、Global Brands、Taiwan Tech OEMs）評分一覽，頂部 Source Mode 標籤 |
| **Comparison** | 雷達圖多公司比較，ASUS legend 首位，預設 3 公司 |
| **Locations** | 地區熱力圖，Taiwan-only / Global Brands 加權顯示 |
| **Scraper** | Chrome 狀態管理、啟動/停止爬蟲、List Type 篩選、公司選擇 |
| **Settings** | URL 清單建立（Office/Country/City/Scan）、Source 欄位顯示、Scraper Config |

---

## 目錄結構

```
glassdoor-dashboard/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI app entry
│       ├── data_loader.py   # CSV/run 讀取邏輯（含 source_mode 正規化）
│       └── api/
│           ├── overview.py  # 評分資料 API
│           ├── ratings.py   # 詳細評分 API
│           ├── scraper.py   # 爬蟲控制 API
│           └── settings.py  # 公司管理、URL 清單建立、Finder 控制 API
├── frontend/
│   └── src/
│       ├── views/           # 頁面元件（Overview/Comparison/Locations/Scraper/Settings）
│       ├── stores/          # Pinia stores（finder store 管理全域任務狀態）
│       ├── api/             # Axios API calls
│       └── App.vue          # 主框架（sidebar + router + 全域狀態列）
└── start.ps1                # 一鍵啟動腳本
```

## 後端 API 重點

| 路徑 | 說明 |
|------|------|
| `POST /settings/finder/office` | 建立 Office URL 清單（對應 `company_finder.py office`） |
| `POST /settings/finder/country` | 建立 Country URL 清單 |
| `POST /settings/finder/scan` | 建立 World Scan 清單 |
| `GET /settings/finder/status` | 查詢目前 Finder 執行狀態與 log |
| `GET /settings/companies` | 列出所有 URL 清單檔案（office/country/scan） |
| `GET /settings/baseline?file=xxx` | 查看某個 URL 清單的內容 |
| `POST /scraper/start` | 啟動爬蟲（支援 `source_mode=office/country/scan/all`） |

## 技術棧

- **Frontend**: Vue 3, Element Plus, ECharts, Pinia, TypeScript
- **Backend**: FastAPI, Pandas, uvicorn
- **Theme**: Dark/Light 可切換（Element Plus `.dark` class + CSS variables）
