# Glassdoor 跨公司地區評分比較工具

從 Glassdoor 自動抓取多家公司各地區的評分數據，以統一的地區基準進行跨公司比較，輸出成 Excel。

---

## 主要腳本

| 腳本 | 用途 |
|------|------|
| `company_finder.py` | **核心工具**：自動探索公司地區 URL、跨公司比對基準地區 |
| `glassdoor_scraper_unified.py` | 爬蟲主程式：進入 Review URL 抓取評分數據，輸出 Excel |
| `config.py` | 設定檔：存放要爬取的公司 Review URL 清單 |
| `啟動Chrome.bat` | 以 remote debug 模式啟動 Chrome（必須先執行） |

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

輸出：`data/glassdoor_ratings.xlsx`

> **`config.py` 的 `INCLUDE_BASELINE` 開關**
> - `True` ：一併抓取基準公司 ASUS 的評分（讀取 `data/asus_locations.json`）
> - `False`：只抓取 `*_matched.json` 內的新公司

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
| Overall | 整體評分 |
| Recommend | 推薦比例 |
| Total Reviews | 評論總數 |
| Diversity & Inclusion | 多元與包容 |
| Work/Life Balance | 工作生活平衡 |
| Compensation and Benefits | 薪酬福利 |
| Culture & Values | 文化價值 |
| Career Opportunities | 職涯機會 |
| Senior Management | 高階管理 |

---

## 注意事項

- 必須保持 Chrome 以 debug 模式開啟（port 9222）並登入 Glassdoor
- Glassdoor 有 paywall，未登入時部分數據會被遮擋
- 各城市頁面之間有 2–3 秒延遲，避免觸發反爬蟲
