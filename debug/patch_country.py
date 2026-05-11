"""
從現有 asus_locations.json 補上 country 欄位，不需要重新爬蟲。
country 來源優先順序：
1. page_heading 裡的括號（如 "ASUS Barcelona (Spain)"）
2. address 最後一段（如 "..., United States"）
"""
import json, re

with open('asus_locations.json', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    country = None
    # 優先從 heading 括號取
    heading = item.get('page_heading') or ''
    m = re.search(r'\(([^)]+)\)', heading)
    if m:
        country = m.group(1).strip()
    # fallback：address 最後一段
    if not country:
        address = item.get('address') or ''
        parts = [p.strip() for p in address.split(',')]
        if len(parts) >= 2:
            country = parts[-1].strip()
    item['country'] = country

with open('asus_locations.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("完成，結果：")
for item in data:
    print(f"  {item['location']:<25} country={item['country']:<20} rating={item['list_rating']}")
