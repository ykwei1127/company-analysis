from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

opts = Options()
opts.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opts)

# 直接開 Jeffersonville Office Locations 頁
driver.get('https://www.glassdoor.com/Location/All-Pegatron-Jeffersonville-Office-Locations-EI_IE337948.4,12_IL.13,27_IC1145141.htm')
time.sleep(4)

print('Title:', driver.title)

# 找 Review 連結
all_links = driver.find_elements(By.TAG_NAME, 'a')
review_links = [(l.text.strip(), l.get_attribute('href')) for l in all_links
                if '/Reviews/' in (l.get_attribute('href') or '') and 'EI_IE' in (l.get_attribute('href') or '')]
print(f'\nReview 連結：{len(review_links)} 個')
for name, href in review_links[:10]:
    print(f'  {name!r} → {href}')
