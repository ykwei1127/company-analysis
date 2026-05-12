"""
找出正確的 ASUS Taiwan IN URL
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import re

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options)

# ASUS slug 長度是 4 ("ASUS"), Taiwan 長度是 6
# 試幾種 IL 組合
slug = "ASUS"
slug_len = 4
city_label = "Taiwan"
city_len = len(city_label)  # 6
il_start = slug_len + 1     # 5
il_end = il_start + city_len  # 11

candidates = [
    f"https://www.glassdoor.com/Reviews/ASUS-Taiwan-Reviews-EI_IE40093.0,{slug_len}_IL.{il_start},{il_end}_IN218.htm",
    f"https://www.glassdoor.com/Reviews/ASUS-Taiwan-Reviews-EI_IE40093.0,4_IL.5,11_IN218.htm",
    # 試 Quanta 已知有效的 IN218，確認 IN code 是對的
    "https://www.glassdoor.com/Reviews/Quanta-Computer-Taiwan-Reviews-EI_IE11939.0,15_IL.16,22_IN218.htm",
]

for url in candidates:
    driver.get(url)
    try:
        WebDriverWait(driver, 8).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    except Exception:
        pass
    cur = driver.current_url
    title = driver.title
    print(f"\nInput:  {url}")
    print(f"Final:  {cur}")
    print(f"Title:  {title}")
    print(f"Match:  {'✅' if 'IN218' in cur and 'Reviews' in cur else '❌ redirect'}")
