# Glassdoor Dashboard

Vue 3 + FastAPI 互動式 Dashboard，用於檢視爬取的 Glassdoor 評分數據、管理公司清單、控制爬蟲。

## 啟動

```powershell
.\start.ps1
```

會同時啟動：
- **Backend** — FastAPI on http://localhost:8000 (uvicorn --reload)
- **Frontend** — Vite dev server on http://localhost:5173

預設 bind `0.0.0.0`，區域網路可用 `http://<IP>:5173` 連入。

## 目錄結構

```
glassdoor-dashboard/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI app entry
│       ├── data_loader.py   # CSV/run 讀取邏輯
│       └── api/
│           ├── overview.py  # 評分資料 API
│           ├── ratings.py   # 詳細評分 API
│           ├── scraper.py   # 爬蟲控制 API
│           └── settings.py  # 設定與公司管理 API
├── frontend/
│   └── src/
│       ├── views/           # 頁面元件
│       ├── stores/          # Pinia stores
│       ├── api/             # Axios API calls
│       └── App.vue          # 主框架（sidebar + router）
└── start.ps1                # 一鍵啟動腳本
```

## 技術棧

- **Frontend**: Vue 3, Element Plus, ECharts, Pinia, TypeScript
- **Backend**: FastAPI, Pandas, uvicorn
- **Theme**: Dark/Light 可切換
