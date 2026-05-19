# Glassdoor 跨公司地區評分比較工具

從 Glassdoor 自動抓取多家公司各地區的評分數據，以統一的地區基準進行跨公司比較，輸出成 Excel。

---

## 主要腳本

| 腳本 | 用途 |
|------|------|
| `company_finder.py` | **核心工具**：自動探索公司地區 URL、跨公司比對基準地區 |
| `glassdoor_scraper_unified.py` | 爬蟲主程式：進入 Review URL 抓取評分數據，輸出 Excel |
| `config.py` | 設定檔：`INCLUDE_BASELINE`、`PARALLEL_PORTS` 等爬蟲參數 |
| `啟動Chrome.bat` | 以 remote debug 模式啟動 Chrome port 9222（單一或平行模式） |
| `啟動Chrome_9223.bat` | 平行模式用：啟動 Chrome port 9223 |
| `啟動Chrome_9224.bat` | 平行模式用：啟動 Chrome port 9224 |
| `debug/test_progress.py` | 測試進度顯示與日誌功能 |
| `debug/fix_taiwan_rows.py` | 修復特定公司 Taiwan 資料 |

---

## 前置條件

```bash
# 建立虛擬環境並安裝依賴
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

每次使用前需先執行 `啟動Chrome.bat`，並在開啟的 Chrome 中登入 Glassdoor。

---

## 完整工作流程

### Step 1：自動探索公司所有地區（首次建立基準）

以 ASUS 為例，`asus_locations.json` 已建立完成，無需重跑。
若需重新探索，編輯 `company_finder.py` 的 `EXPLORE_CONFIG` 後執行：

```bash
venv\Scripts\python company_finder.py explore
```

輸出：`{公司名}_locations.json`，包含所有辦公室城市的地區 Review URL。

---

### Step 2：對新公司比對 22 個基準地區

ASUS 的 22 個有效地區為比較基準（存於 `asus_locations.json`）。

在 `company_finder.py` 的 `COMPANIES_TO_MATCH` 填入公司名稱（只需填名稱，ID 和 URL 自動搜尋）：

```python
COMPANIES_TO_MATCH = [
    'Nvidia',
    'MSI',
]
```

執行：

```bash
venv\Scripts\python company_finder.py match
```

輸出：`{公司名}_matched.json`，每個基準地區會標記：

| status | 說明 |
|--------|------|
| `found` | 找到該地區的 Review URL |
| `no_review_url` | 該公司在此國家有辦公室，但無地區 Review 頁 |
| `not_in_company` | 該公司在此國家無辦公室 |

---

### Step 3：抓取評分數據

`company_finder.py match` 執行完後，`data/` 目錄下會有 `*_matched.json`。
直接執行爬蟲，會自動讀取所有 matched JSON（**不需要手動更新 `config.py`**）：

```bash
venv\Scripts\python glassdoor_scraper_unified.py
```

輸出：`output/glassdoor_ratings.xlsx` 和 `output/glassdoor_ratings.csv`
每次執行也會在 `logs/` 目錄產生 `.txt`（完整 log）和 `.json`（摘要報告），並自動將各 port 的詳細 log 合併。

> **`config.py` 相關開關**
>
> | 設定 | 說明 |
> |------|------|
> | `INCLUDE_BASELINE = True` | 一併抓取基準公司 ASUS 的評分（讀取 `data/asus_locations.json`） |
> | `INCLUDE_BASELINE = False` | 只抓取 `*_matched.json` 內的新公司 |
> | `PARALLEL_PORTS = [9222, 9223, 9224]` | 平行模式：3 個 Chrome 同時抓，約 3x 加速，顯示 tqdm 進度條 |
> | `PARALLEL_PORTS = [9222]` | 單一模式：只用一個 Chrome（預設） |

**平行模式使用步驟：**
1. 分別執行 `啟動Chrome.bat`、`啟動Chrome_9223.bat`、`啟動Chrome_9224.bat`
2. 每個 Chrome 視窗都登入 Glassdoor
3. 確認 `config.py` 的 `PARALLEL_PORTS = [9222, 9223, 9224]`
4. 執行爬蟲

---

## 22 個基準地區（來自 ASUS）

| 城市 | 國家 |
|------|------|
| Global | — |
| Fremont, CA | United States |
| Markham, ON | Canada |
| Barcelona | Spain |
| Budapest | Hungary |
| Emmen | Netherlands |
| Hemel Hempstead | United Kingdom |
| Milan | Italy |
| Noisy-le-Grand | France |
| Ratingen | Germany |
| Bangkok | Thailand |
| Dubai | United Arab Emirates |
| Jakarta | Indonesia |
| Kuala Lumpur | Malaysia |
| Manila | Philippines |
| Mumbai | India |
| Seoul | South Korea |
| Singapore | Singapore |
| Taipei | Taiwan |
| Tokyo | Japan |
| Santiago | Chile |
| São Paulo | Brazil |
| Sydney | Australia |

---

## 輸出 Excel 欄位

| 欄位 | 說明 |
|------|------|
| Company | 公司名稱 |
| Baseline Location | 比較基準地區（來自 ASUS 22 個地區） |
| Country | 基準地區的國家 |
| Actual City | 實際抓取的城市（與新公司 Glassdoor 的辦公室對應，可能與基準不同） |
| Review URL | 該筆資料對應的 Glassdoor Review 頁面 URL |
| Overall | 整體評分 |
| Recommend | 推薦比例 |
| CEO Approval | CEO 支持率 |
| Total Reviews | 評論總數 |
| Diversity & Inclusion | 多元與包容 |
| Work/Life Balance | 工作生活平衡 |
| Compensation and Benefits | 薪酬福利 |
| Culture & Values | 文化價值 |
| Career Opportunities | 職涯機會 |
| Senior Management | 高階管理 |

---

## Web Dashboard

互動式 Dashboard，可在瀏覽器中檢視評分數據、啟動爬蟲、管理公司清單。

### 啟動方式

```powershell
cd glassdoor-dashboard
.\start.ps1
```

- **Frontend**: http://localhost:5173（Vue 3 + Element Plus）
- **Backend**: http://localhost:8000/docs（FastAPI）
- 預設 bind `0.0.0.0`，區域網路其他電腦可用 `http://<你的IP>:5173` 連入

### 頁面功能

| 頁面 | 說明 |
|------|------|
| Overview | 各公司 Global 評分一覽 |
| Comparison | 雷達圖跨公司比較 |
| Locations | 地區評分熱力圖 |
| Scraper | Chrome 狀態、啟動/停止爬蟲、即時 log |
| Settings | 公司管理（新增/刪除/Match/Explore）、Baseline 地區、爬蟲設定 |

### 刪除爬取紀錄

在頂部 run 下拉選單旁的 🗑️ 按鈕可刪除選中的 run（CSV、XLSX、log 全部刪除）。

---

## 注意事項

- 必須保持 Chrome 以 debug 模式開啟並登入 Glassdoor（單一模式用 port 9222；平行模式需同時開 9222/9223/9224）
- Glassdoor 有 paywall，未登入時部分數據會被遮擋
- 各城市頁面之間採動態延遲：成功抓取 1.5s，失敗 0.5s，優化整體速度
- Cloudflare 偵測：頁面載入後若 title 為 "Just a moment..." 會自動等待最多 5 秒讓 JS challenge 通過
- 若 Cloudflare 真正攔截（需人工驗證），scraper 會暫停該 port 並將任務轉移給其他 port
- 日誌即時 flush 到磁碟，crash 不會丟失已完成的紀錄
- 若搜尋到的公司 ID 有誤（如 Compal Electronics 誤抓為 Delta Electronics），`company_finder.py` 會以 `all()` 比對所有關鍵字避免誤判，但仍建議執行後確認 `*_matched.json` 的 Global URL 是否正確
