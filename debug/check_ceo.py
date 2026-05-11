from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

opts = Options()
opts.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opts)

driver.get('https://www.glassdoor.com/Overview/Working-at-AU-Optronics-EI_IE16126.11,23.htm')
time.sleep(4)

# 找包含 approve 的元素
all_elems = driver.find_elements(By.XPATH, '//*[contains(text(), "approve")]')
print(f'找到 {len(all_elems)} 個含 approve 的元素')
for e in all_elems[:5]:
    print(f'  tag={e.tag_name} class={e.get_attribute("class")!r} text={e.text!r}')

# 找包含 % 且在 CEO 附近的元素
print()
ceo_elems = driver.find_elements(By.XPATH, '//*[contains(text(), "CEO")]')
print(f'找到 {len(ceo_elems)} 個含 CEO 的元素')
for e in ceo_elems[:5]:
    print(f'  tag={e.tag_name} class={e.get_attribute("class")!r} text={e.text!r}')
