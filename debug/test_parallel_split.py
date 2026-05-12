"""
測試 ASUS baseline 拆分後的平行邏輯
只跑 Global + Fremont 兩筆，確認：
1. location_filter 正確過濾
2. 各 port log 分開
3. 結果資料正確
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from glassdoor_scraper_unified import GlassdoorScraper

PORT = 9222
JSON = 'data/asus_locations.json'

# 測試 1：location_filter = 'Global'
print("=== 測試 location_filter='Global' ===")
s = GlassdoorScraper(mode='manual', chrome_debugger_port=PORT)
r = s.scrape_from_baseline_json(JSON, company_name='ASUS', location_filter='Global')
s.close()
print(f"筆數: {len(r)} (應為 1)")
if r:
    print(f"Baseline Location: {r[0].get('Baseline Location')}")
    print(f"Overall: {r[0].get('Overall')}")
    print(f"Review URL: {r[0].get('Review URL')}")

print()

# 測試 2：location_filter = 'Fremont, CA'
print("=== 測試 location_filter='Fremont, CA' ===")
s = GlassdoorScraper(mode='manual', chrome_debugger_port=PORT)
r = s.scrape_from_baseline_json(JSON, company_name='ASUS', location_filter='Fremont, CA')
s.close()
print(f"筆數: {len(r)} (應為 1)")
if r:
    print(f"Baseline Location: {r[0].get('Baseline Location')}")
    print(f"Overall: {r[0].get('Overall')}")

print()

# 測試 3：location_filter = None → 應全部跑（只印數量，不實際跑完）
print("=== 測試 location_filter=None 下第一筆 ===")
import json
with open(JSON, encoding='utf-8') as f:
    entries = json.load(f)
found = [e for e in entries if e.get('status') == 'found' and e.get('url')]
print(f"應跑筆數: {len(found)}")
print("(不實際全跑，避免太慢)")
