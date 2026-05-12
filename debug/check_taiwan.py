import json, glob

print(f"{'公司':<25} {'Matched City':<25} {'URL'}")
print('-' * 100)
for path in sorted(glob.glob('data/*_matched.json')):
    with open(path, encoding='utf-8') as f:
        entries = json.load(f)
    for e in entries:
        if e.get('baseline_location') == 'Taipei, TPQ':
            company = e['company']
            url = e.get('url') or '❌ 無'
            city = e.get('matched_city') or '❌ 無'
            print(f"{company:<25} {city:<25} {url}")
