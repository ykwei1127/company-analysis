"""
確認 Glassdoor Taiwan 整體 Review URL 格式
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time, re

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options)

# 已知 Quanta 有 Taiwan 整體 URL
test_urls = [
    "https://www.glassdoor.com/Reviews/Quanta-Computer-Taiwan-Reviews-EI_IE11939.0,15_IL.16,22_IN218.htm",
    "https://www.glassdoor.com/Reviews/ASUS-Taiwan-Reviews-EI_IE40093.0,4_IL.5,11_IN218.htm",
]

for url in test_urls:
    driver.get(url)
    try:
        WebDriverWait(driver, 8).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    except Exception:
        pass
    cur = driver.current_url
    title = driver.title
    in_match = re.search(r'_IN(\d+)', cur)
    print(f"\nURL: {url}")
    print(f"Final: {cur}")
    print(f"Title: {title}")
    print(f"IN code: {in_match.group(1) if in_match else 'N/A'}")
    print(f"Valid: {'✅' if '_IN' in cur else '❌'}")
    time.sleep(2)
