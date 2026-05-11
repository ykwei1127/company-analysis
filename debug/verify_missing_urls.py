"""
驗證 5 個 no_review_url 城市是否真的沒有 review 頁面
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

CHROME_DEBUG_PORT = 9222

MISSING_CITIES = [
    ('Ciudad de Mexico', 'https://www.glassdoor.com/Location/All-ASUS-Ciudad-de-Mexico-Office-Locations-EI_IE40093.4,8_IL.9,25_IC5017436.htm'),
    ('Moravska Ostrava', 'https://www.glassdoor.com/Location/All-ASUS-Moravsk%C3%A1-Ostrava-Office-Locations-EI_IE40093.4,8_IL.9,27.htm'),
    ('San Isidro',       'https://www.glassdoor.com/Location/All-ASUS-San-Isidro-Office-Locations-EI_IE40093.4,8_IL.9,18_IC3526581.htm'),
    ('Warsaw',           'https://www.glassdoor.com/Location/All-ASUS-Warsaw-Office-Locations-EI_IE40093.4,8_IL.9,15_IC2524548.htm'),
    ('Uskudar',          'https://www.glassdoor.com/Location/All-ASUS-Uskudar-Office-Locations-EI_IE40093.4,8_IL.9,15_IC3208178.htm'),
]

NUMERIC_ID = '40093'

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{CHROME_DEBUG_PORT}")
driver = webdriver.Chrome(options=chrome_options)

for city, url in MISSING_CITIES:
    print(f"\n{'='*50}")
    print(f"城市：{city}")
    print(f"URL：{url}")
    driver.get(url)
    time.sleep(4)

    all_links = driver.find_elements(By.TAG_NAME, 'a')
    review_links = []
    for link in all_links:
        href = link.get_attribute('href') or ''
        text = link.text.strip()
        if '/Reviews/' in href and NUMERIC_ID in href:
            review_links.append((text, href))

    if review_links:
        print(f"  ✅ 找到 {len(review_links)} 個 Review 連結：")
        for text, href in review_links:
            print(f"    TEXT: {repr(text)}")
            print(f"    HREF: {href}")
    else:
        print(f"  ❌ 確認無 Review 連結")

print("\n完成")
