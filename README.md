# Glassdoor 跨公司地區評分比較工具

從 Glassdoor 自動抓取多家公司各地區的評分數據，以統一的地區基準進行跨公司比較，輸出成 Excel。

---

## 主要腳本

| 腳本 | 用途 |
|------|------|
| `company_finder.py` | **核心工具**：建立公司地區 Review URL 清單（office/country/scan 三種模式） |
| `glassdoor_scraper_unified.py` | 爬蟲主程式：進入 Review URL 抓取評分數據，輸出 Excel |
| `config.py` | 設定檔：`INCLUDE_BASELINE`、`PARALLEL_PORTS` 等爬蟲參數 |
| `migrate_filenames.py` | 一次性遷移腳本：將舊命名（`_matched.json`）改成新命名（`_office.json`） |
| `啟動Chrome.bat` | 以 remote debug 模式啟動 Chrome port 9222 |
| `啟動Chrome_9223.bat` | 平行模式用：啟動 Chrome port 9223 |
| `啟動Chrome_9224.bat` | 平行模式用：啟動 Chrome port 9224 |

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

### Phase 1：建立 URL 清單（每種類型只需執行一次）

URL 清單是爬蟲的來源，決定「要抓哪些地區的哪些公司評分」。共有三種類型：

#### 1a. Office Location 清單
從 Glassdoor 辦公室頁面收集城市級別 Review URL：

```bash
venv\Scripts\python company_finder.py office
```

輸出：`data/{公司名}_office.json`，包含所有辦公室城市的 Review URL。

#### 1b. Country 清單
使用國家 IN 代碼建立國家級別 Review URL（快速、一致性高，**推薦**）：

```bash
venv\Scripts\python company_finder.py country
```

輸出：`data/{公司名}_country.json`，每個基準國家的 Review URL。

#### 1c. World Scan 清單（可選）
掃描全球 60+ 個國家，探索該公司在哪些地區有評論：

```bash
venv\Scripts\python company_finder.py scan
```

輸出：`data/{公司名}_scan.json`，標記各國是否有評論。

---

### Phase 2：抓取評分數據（定期執行）

URL 清單建好後，直接執行爬蟲。爬蟲自動讀取 `data/` 下所有 `*_office.json`、`*_country.json`、`*_scan.json`：

```bash
venv\Scripts\python glassdoor_scraper_unified.py
```

輸出：`output/glassdoor_ratings.xlsx`、`output/glassdoor_ratings.csv`  
每次執行也會在 `logs/` 產生 `.txt`（完整 log）和 `.json`（摘要）。

> **`config.py` 相關開關**
>
> | 設定 | 說明 |
> |------|------|
> | `INCLUDE_BASELINE = True` | 一併抓取 ASUS office 清單（讀取 `data/asus_office.json`） |
> | `INCLUDE_BASELINE = False` | 只抓取其他 URL 清單 |
> | `PARALLEL_PORTS = [9222, 9223, 9224]` | 平行模式：3 個 Chrome 同時抓，約 3x 加速 |
> | `PARALLEL_PORTS = [9222]` | 單一模式（預設） |

**平行模式使用步驟：**
1. 分別執行 `啟動Chrome.bat`、`啟動Chrome_9223.bat`、`啟動Chrome_9224.bat`
2. 每個 Chrome 視窗都登入 Glassdoor
3. 確認 `config.py` 的 `PARALLEL_PORTS = [9222, 9223, 9224]`
4. 執行爬蟲

---

## 在 `COMPANIES_TO_MATCH` 新增公司

編輯 `company_finder.py` 中的 `COMPANIES_TO_MATCH`（只需填名稱，ID/URL 自動搜尋）：

```python
COMPANIES_TO_MATCH = [
    'Nvidia',
    'MSI',
    # 也可以手動指定 ID 避免搜尋誤判：
    {"name": "HP Inc.", "company_id": "E1093161", "slug": "HP-Inc"},
]
```

或使用 Dashboard Settings 頁面動態新增。

---

## 三種 URL 清單類型對照

| 類型 | 命名 | 說明 | 比對依據 |
|------|------|------|---------|
| **Office** | `*_office.json` | Glassdoor 辦公室頁面的城市級別 URL | ASUS 辦公室地點 |
| **Country** | `*_country.json` | 國家級別 URL（IN 代碼） | ASUS 辦公室所在國家 |
| **Scan** | `*_scan.json` | 全球掃描結果 | 60+ 個國家 |

ASUS 的基準檔案：`data/asus_office.json`（29 個條目：27 城市 + Global + Taiwan 國家級）

---

## 基準地區（來自 ASUS）

| 類型 | 地點 | 國家 |
|------|------|------|
| 🌐 Global | Global | — |
| 🇹🇼 Country | Taiwan | Taiwan |
| 🏢 City | Fremont, CA | United States |
| | Markham, ON | Canada |
| | Barcelona | Spain |
| | Budapest | Hungary |
| | Emmen | Netherlands |
| | Hemel Hempstead | United Kingdom |
| | Milan | Italy |
| | Noisy-le-Grand | France |
| | Ratingen | Germany |
| | Bangkok | Thailand |
| | Dubai | United Arab Emirates |
| | Jakarta | Indonesia |
| | Kuala Lumpur | Malaysia |
| | Manila | Philippines |
| | Mumbai | India |
| | Seoul | South Korea |
| | Singapore | Singapore |
| | Taipei | Taiwan |
| | Tokyo | Japan |
| | Santiago | Chile |
| | São Paulo | Brazil |
| | Sydney | Australia |

---

## 輸出 Excel 欄位

| 欄位 | 說明 |
|------|------|
| Company | 公司名稱 |
| Baseline Location | 比較基準地區 |
| Country | 基準地區的國家 |
| Actual City | 實際抓取的城市 |
| Review URL | Glassdoor Review 頁面 URL |
| Source Mode | URL 清單類型（office / country / scan） |
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

互動式 Dashboard，可在瀏覽器中檢視評分數據、建立 URL 清單、啟動爬蟲。

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
| Overview | 各公司 Global 評分一覽，顯示 List Type 標籤 |
| Comparison | 雷達圖跨公司比較 |
| Locations | 地區評分熱力圖 |
| Scraper | Chrome 狀態、啟動/停止爬蟲、**List Type 篩選**、公司選擇 |
| Settings | 公司管理、**建立 URL 清單**（Office/Country/Scan）、查看清單內容 |

### List Type（URL 清單類型）

| 類型 | 說明 | 使用時機 |
|------|------|----------|
| **Office** | 從 Glassdoor 辦公室頁面抓城市級別 URL | 城市精確比對 |
| **Country** | 國家級別 IN 代碼 URL | 推薦！快速、一致性高 |
| **World Scan** | 掃描 60+ 國家 | 探索新區域或驗證覆蓋率 |

### 刪除爬取紀錄

在頂部 run 下拉選單旁的 🗑️ 按鈕可刪除選中的 run（CSV、XLSX、log 全部刪除）。

---

## 注意事項

- 必須保持 Chrome 以 debug 模式開啟並登入 Glassdoor（單一模式 port 9222；平行模式需同時開 9222/9223/9224）
- **URL 清單每種類型只需建一次**，後續只用 Scraper 定期抓評分結果
- **Baseline 結構**：`asus_office.json` 包含 27 城市 + Global + Taiwan，共 29 個條目
- **全局狀態**：頂部狀態欄顯示正在執行的任務，任何頁面都可見
- Glassdoor 有 paywall，未登入時部分數據會被遮擋
- Cloudflare 偵測：頁面載入後若 title 為 "Just a moment..." 會自動等待最多 5 秒
- 若 Cloudflare 真正攔截，scraper 會暫停該 port 並將任務轉移給其他 port
- 日誌即時 flush 到磁碟，crash 不會丟失已完成的紀錄
