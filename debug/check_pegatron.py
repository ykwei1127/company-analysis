from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

opts = Options()
opts.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opts)

driver.get('https://www.glassdoor.com/Location/All-Pegatron-Office-Locations-E337948.htm')
time.sleep(4)

links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/Reviews/"]')
us_links = [(l.text, l.get_attribute('href')) for l in links if 'United-States' in (l.get_attribute('href') or '') or '_IC11' in (l.get_attribute('href') or '')]

all_links = [(l.text.strip(), l.get_attribute('href')) for l in links if l.text.strip()]
print(f'全部 Review 連結：{len(all_links)} 個')
for name, href in all_links[:30]:
    print(f'  {name:<30} {href}')
