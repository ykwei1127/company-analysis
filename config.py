# Glassdoor 爬蟲配置文件

# ============================================
# 是否也抓取基準公司（ASUS）的評分
# True  = 一併抓取 data/asus_locations.json 中有 URL 的地區
# False = 只抓 *_matched.json（新公司）
# ============================================
INCLUDE_BASELINE = True

# ============================================
# 爬蟲設定
# ============================================
SCRAPER_CONFIG = {
    # 模式選擇：
    # 'manual' = 連接到已登入的 Chrome（推薦，避免反爬蟲）
    # 'auto' = 自動啟動新的 Chrome（可能遇到人機驗證）
    'mode': 'manual',
    
    # 是否隱藏瀏覽器視窗（僅在 auto 模式下有效）
    'headless': False,
    
    # 頁面載入等待時間（秒）
    'wait_time': 5,
    
    # 請求之間的延遲（秒）
    'delay_between_requests': 3,
}

# ============================================
# 輸出設定
# ============================================
OUTPUT_CONFIG = {
    # 輸出檔案名稱
    'filename': 'data/glassdoor_ratings.xlsx',
    
    # Excel 工作表名稱
    'sheet_name': 'Ratings',
}

# ============================================
# 如何添加新公司
# ============================================
# 在 company_finder.py 的 COMPANIES_TO_MATCH 填入公司名稱即可，
# ID 和 URL 會自動從 Glassdoor 搜尋，不需要在此手動維護。
#
# 範例：
#   COMPANIES_TO_MATCH = [
#       'TSMC',
#       'NVIDIA',
#   ]
