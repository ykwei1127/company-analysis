"""
測試：用 IC Code 直接拼 URL 並驗證是否存在
以 Quanta Computer (E11939) + Taipei (IC3271041) 為例
"""
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options)

# Quanta 的已知資訊
numeric_id = '11939'
slug = 'Quanta-Computer'
company_name_len = len('Quanta-Computer')  # 15

# Taipei IC Code（從 ASUS URL 抽取）
test_cases = [
    ('Taipei', 'IC3271041'),
    ('Singapore', 'IC3235921'),
    ('Tokyo', 'IC2851580'),
]

for city_name, ic_code in test_cases:
    ic_num = ic_code.replace('IC', '')
    # IL 參數 = slug 長度的起終位置（公司名後面接城市）
    # 格式：EI_IE{id}.0,{slug_len}_IL.{slug_len+1},{slug_len+1+city_len}_IC{ic}
    city_len = len(city_name)
    il_start = company_name_len + 1
    il_end = il_start + city_len
    url = (f"https://www.glassdoor.com/Reviews/{slug}-{city_name}-Reviews"
           f"-EI_IE{numeric_id}.0,{company_name_len}"
           f"_IL.{il_start},{il_end}_IC{ic_num}.htm")
    print(f"\n{city_name}: {url}")
    driver.get(url)
    time.sleep(3)
    # 確認頁面標題
    title = driver.title
    cur = driver.current_url
    print(f"  Title: {title}")
    print(f"  URL:   {cur}")
    if 'Reviews' in cur and ic_num in cur:
        print(f"  ✅ 有效")
    elif 'glassdoor.com' in cur:
        print(f"  ❌ 被導向其他頁")
    else:
        print(f"  ❌ 無效")
