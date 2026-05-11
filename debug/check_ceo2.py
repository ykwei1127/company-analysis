from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

opts = Options()
opts.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opts)

# 試 Reviews 頁面有沒有 CEO 資料
driver.get('https://www.glassdoor.com/Reviews/NVIDIA-Reviews-E7633.htm')
time.sleep(5)

elems = driver.find_elements(By.XPATH, '//*[contains(text(), "approve")]')
print(f'Reviews 頁：找到 {len(elems)} 個含 approve 的元素')
for e in elems[:3]:
    print(f'  tag={e.tag_name} class={e.get_attribute("class")!r} text={e.text!r}')

# 試 Global reviews 頁有沒有 Overview 連結
overview_links = driver.find_elements(By.XPATH, '//a[contains(@href, "/Overview/")]')
print(f'\nOverview 連結：{len(overview_links)} 個')
for l in overview_links[:3]:
    print(f'  {l.get_attribute("href")}')
