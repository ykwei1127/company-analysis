"""
debug 用：印出 Office Locations 頁面上所有連結，找出 review URL 的真實格式
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

CHROME_DEBUG_PORT = 9222
URL = 'https://www.glassdoor.com/Location/All-ASUS-Office-Locations-E40093.htm'

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{CHROME_DEBUG_PORT}")
driver = webdriver.Chrome(options=chrome_options)

print(f"載入頁面：{URL}")
driver.get(URL)
time.sleep(5)

# 完整滾動
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# 抓所有 <a> 連結
all_links = driver.find_elements(By.TAG_NAME, 'a')
print(f"\n頁面共有 {len(all_links)} 個連結\n")

print("=== 含有 glassdoor.com 的連結 ===")
for link in all_links:
    href = link.get_attribute('href') or ''
    text = link.text.strip()
    if 'glassdoor' in href.lower() and href:
        print(f"TEXT: {repr(text)}")
        print(f"HREF: {href}")
        print()

# 也印出頁面 title 確認是對的頁面
print(f"\n頁面 title：{driver.title}")
print(f"當前 URL：{driver.current_url}")
