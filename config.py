# Glassdoor 爬蟲配置文件
# 修改此文件來自訂要抓取的公司

# ============================================
# 要抓取的公司列表
# ============================================
COMPANY_URLS = {
    # ASUS 相關
    'ASUS reviews': 'https://www.glassdoor.com/Reviews/ASUS-Reviews-E40093.htm',
    'ASUS Taipei reviews': 'https://www.glassdoor.com/Reviews/ASUS-Taipei-Reviews-EI_IE40093.0,4_IL.5,11_IC3271041.htm',
    'ASUS Taiwan reviews': 'https://www.glassdoor.com/Reviews/ASUS-Taiw%C3%A1n-Reviews-EI_IE40093.0,4_IL.5,11_IN240.htm',
    'ASUS Singapore reviews': 'https://www.glassdoor.com/Reviews/ASUS-Singapore-Reviews-EI_IE40093.0,4_IL.5,14_IN217.htm',
    'ASUS India reviews': 'https://www.glassdoor.com/Reviews/ASUS-India-Reviews-EI_IE40093.0,4_IL.5,10_IN115.htm',
    
    # Nvidia
    'Nvidia reviews': 'https://www.glassdoor.com/Reviews/NVIDIA-Reviews-E7633.htm',
    'Nvidia Taipei reviews': 'https://www.glassdoor.com/Reviews/NVIDIA-Taipei-Reviews-EI_IE7633.0,6_IL.7,13_IC3271041.htm',
    'Nvidia Taiwan reviews': 'https://www.glassdoor.com/Reviews/NVIDIA-Taiwan-Reviews-EI_IE7633.0,6_IL.7,13_IN240.htm',
    'Nvidia Singapore reviews': 'https://www.glassdoor.com/Reviews/NVIDIA-Singapore-Reviews-EI_IE7633.0,6_IL.7,16_IM1123.htm',
    'Nvidia India reviews': 'https://www.glassdoor.com/Reviews/NVIDIA-India-Reviews-EI_IE7633.0,6_IL.7,12_IN115.htm',

    # Acer Group
    'Acer Group reviews': 'https://www.glassdoor.com/Reviews/Acer-Group-Reviews-E3802.htm',
    'Acer Group Taipei reviews': 'https://www.glassdoor.com/Reviews/Acer-Group-Taipei-Reviews-EI_IE3802.0,10_IL.11,17_IC3271041.htm',
    'Acer Group Taiwan reviews': '',
    'Acer Group Singapore reviews': 'https://www.glassdoor.com/Reviews/Acer-Group-Singapore-Reviews-EI_IE3802.0,10_IL.11,20_IM1123.htm',
    'Acer Group Bangalore reviews': 'https://www.glassdoor.co.in/Reviews/Acer-Group-Bangalore-Reviews-EI_IE3802.0,10_IL.11,20_IM1091.htm',

    # MSI (Micro-Star International)
    'MSI reviews': 'https://www.glassdoor.com/Reviews/MSI-Reviews-E750335.htm',
    'MSI Taipei reviews': 'https://www.glassdoor.com/Reviews/MSI-Taipei-Reviews-EI_IE750335.0,3_IL.4,10_IC3271041.htm',
    'MSI Taiwan reviews': '',
    'MSI Singapore reviews': 'https://www.glassdoor.com/Reviews/MSI-Global-Singapore-Reviews-E310403.htm',
    'MSI Bangalore reviews': 'https://www.glassdoor.com/Reviews/MSI-Bengaluru-Reviews-EI_IE750335.0,3_IL.4,13_IC2940587.htm',

    # Wistron
    'Wistron reviews': 'https://www.glassdoor.com/Reviews/Wistron-Reviews-E15218.htm',
    'Wistron Taipei reviews': 'https://www.glassdoor.com/Reviews/Wistron-Taipei-Reviews-EI_IE15218.0,7_IL.8,14.htm',
    'Wistron Taiwan reviews': 'https://www.glassdoor.com/Reviews/Wistron-Taiwan-Reviews-EI_IE15218.0,7_IL.8,14_IN240.htm',
    'Wistron Singapore reviews': '',
    'Wistron Bangalore reviews': 'https://www.glassdoor.com/Reviews/Wistron-Bangalore-Reviews-EI_IE15218.0,7_IL.8,17_IM1091.htm',

    # TSMC
    'TSMC reviews': 'https://www.glassdoor.com/Reviews/TSMC-Reviews-E4130.htm',
    'TSMC Taipei reviews': 'https://www.glassdoor.com/Reviews/Taipei-Reviews-EI_IE4130_IL.0,6.htm',
    'TSMC Taiwan reviews': 'https://www.glassdoor.com/Reviews/TSMC-Taiwan-Reviews-EI_IE4130.0,4_IL.5,11_IN240.htm',
    'TSMC Singapore reviews': 'https://www.glassdoor.com/Reviews/TSMC-Singapore-Reviews-EI_IE4130.0,4_IL.5,14_IC3235921.htm',
    'TSMC India reviews': '',

    # Quanta Computer
    'Quanta Computer reviews': 'https://www.glassdoor.com/Reviews/Quanta-Computer-Reviews-E11939.htm',
    'Quanta Computer Taipei reviews': 'https://www.glassdoor.com/Reviews/Quanta-Computer-Taipei-Reviews-EI_IE11939.0,15_IL.16,22_IC3271041.htm',
    'Quanta Computer Taiwan reviews': 'https://www.glassdoor.com/Reviews/Quanta-Computer-Taiwan-Reviews-EI_IE11939.0,15_IL.16,22_IN240.htm',
    'Quanta Computer Singapore reviews': '',
    'Quanta Computer India reviews': '',

    # Wiwynn
    'Wiwynn reviews': 'https://www.glassdoor.com/Reviews/Wiwynn-Reviews-E1161475.htm',
    'Wiwynn Taipei reviews': 'https://www.glassdoor.com/Reviews/Wiwynn-Taipei-Reviews-EI_IE1161475.0,6_IL.7,13_IC3271041.htm',
    'Wiwynn Taiwan reviews': '',
    'Wiwynn Singapore reviews': '',
    'Wiwynn India reviews': '',

    # Compal Electronics
    'Compal Electronics reviews': 'https://www.glassdoor.com/Reviews/Compal-Electronics-Reviews-E13464.htm',
    'Compal Electronics Taipei reviews': '',
    'Compal Electronics Taiwan reviews': 'https://www.glassdoor.com/Reviews/Compal-Electronics-Taiwan-Reviews-EI_IE13464.0,18_IL.19,25_IN240.htm',
    'Compal Electronics Singapore reviews': '',
    'Compal Electronics India reviews': '',


    # 添加更多公司範例（取消註解即可使用）
    # 'Google': 'https://www.glassdoor.com/Reviews/Google-Reviews-E9079.htm',
    # 'Microsoft': 'https://www.glassdoor.com/Reviews/Microsoft-Reviews-E1651.htm',
    # 'Apple': 'https://www.glassdoor.com/Reviews/Apple-Reviews-E1138.htm',
    # 'Amazon': 'https://www.glassdoor.com/Reviews/Amazon-Reviews-E6036.htm',
}

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
    'filename': 'glassdoor_ratings.xlsx',
    
    # Excel 工作表名稱
    'sheet_name': 'Ratings',
}

# ============================================
# 如何添加新公司
# ============================================
"""
步驟 1: 在 Glassdoor 上找到公司評論頁面
        例如：https://www.glassdoor.com/Reviews/公司名稱-Reviews-E公司ID.htm

步驟 2: 複製 URL

步驟 3: 在上方 COMPANY_URLS 字典中添加：
        '顯示名稱': 'URL',

範例：
    'Tesla': 'https://www.glassdoor.com/Reviews/Tesla-Reviews-E43129.htm',
    'Netflix': 'https://www.glassdoor.com/Reviews/Netflix-Reviews-E11891.htm',

注意：
- 每一行結尾要有逗號
- URL 要用引號包起來
- 顯示名稱會出現在 Excel 的 Company 欄位
"""
