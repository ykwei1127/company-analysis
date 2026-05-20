# Glassdoor Dashboard

Vue 3 + FastAPI 互動式 Dashboard，用於檢視爬取的 Glassdoor 評分數據、建立 URL 清單、控制爬蟲。

## 啟動

```powershell
.\start.ps1
```

會同時啟動：
- **Backend** — FastAPI on http://localhost:8000 (uvicorn --reload)
- **Frontend** — Vite dev server on http://localhost:5173

預設 bind `0.0.0.0`，區域網路可用 `http://<IP>:5173` 連入。

## 頁面說明

| 頁面 | 功能 |
|------|------|
| **Overview** | 各公司 Global 評分一覽，顯示 List Type 標籤，支援混合類型警告 |
| **Comparison** | 雷達圖多公司比較，可選擇地區與公司 |
| **Locations** | 地區評分熱力圖，按地點與公司過濾 |
| **Scraper** | Chrome 狀態管理、啟動/停止爬蟲、**List Type 篩選**、公司選擇 |
| **Settings** | 建立 URL 清單（Office/Country/Scan）、公司管理、查看清單內容、Scraper Config |

## URL 清單工作流程

Settings 頁面分三種 URL 清單類型（每種只需建一次）：

| 類型 | 說明 | 輸出檔案 |
|------|------|---------|
| **Office Location** | 從 Glassdoor 辦公室頁面抓城市級別 URL | `data/*_office.json` |
| **Country** | 國家級別 IN 代碼 URL（推薦） | `data/*_country.json` |
| **World Scan** | 掃描 60+ 個國家 | `data/*_scan.json` |

URL 清單建好後，到 **Scraper 頁面**選擇 List Type 後啟動爬蟲定期抓取評分。

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
- **Theme**: Dark/Light 可切換
