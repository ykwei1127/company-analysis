from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

opts = Options()
opts.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opts)

driver.get('https://www.glassdoor.com/Location/All-Pegatron-Office-Locations-E337948.htm')
time.sleep(4)

print('Page title:', driver.title)
print('Current URL:', driver.current_url)

# 找所有 a 連結裡含城市/location 相關的
all_links = driver.find_elements(By.TAG_NAME, 'a')
location_links = [(l.text.strip(), l.get_attribute('href')) for l in all_links
                  if l.get_attribute('href') and 'Location' in (l.get_attribute('href') or '')]
print(f'\nLocation 連結：{len(location_links)} 個')
for name, href in location_links[:20]:
    print(f'  {name:<30} {href[:80]}')

# 看有沒有 Jeffersonville 相關
jeff_links = [(l.text.strip(), l.get_attribute('href')) for l in all_links
              if 'Jeffersonville' in (l.get_attribute('href') or '') or 'Jeffersonville' in l.text]
print(f'\nJeffersonville 連結：{len(jeff_links)} 個')
for name, href in jeff_links:
    print(f'  {name} → {href}')
