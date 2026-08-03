"""
快速測試：只跑 6 筆（每 port 2 筆），驗證進度顯示和即時 flush
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from glassdoor_scraper_unified import parallel_scrape

# 只選 3 家公司的 Global + 一個地區，共 6 筆
test_files = [
    'data/nvidia_matched.json',
    'data/tsmc_matched.json',
    'data/wistron_matched.json',
]

print("=" * 50)
print("測試項目：")
print("1. 每 5 秒應看到進度條更新")
print("2. logs/run_*_port*.txt 應即時寫入（可開另一視窗觀察）")
print("3. 成功筆應 sleep 1.5s，失敗筆 0.5s")
print("=" * 50)
print("\n請確認 Chrome ports 9222/9223/9224 已登入，5 秒後自動開始...")
import time
time.sleep(5)

# 手動建立 tasks，只取每家前 2 筆（Global + 一個地區）
import json

tasks_all = []
for f in test_files:
    with open(f, encoding='utf-8') as fp:
        entries = json.load(fp)
    # 取前 2 筆 found 的
    count = 0
    for e in entries:
        if e.get('status') == 'found' and e.get('url') and count < 2:
            tasks_all.append({'type': 'matched', 'file': f})
            count += 1

print(f"\n共 {len(tasks_all)} 筆任務，預計 1-2 分鐘完成\n")

# 呼叫 parallel_scrape（include_baseline=False 跳過 ASUS）
data = parallel_scrape(
    ports=[9222, 9223, 9224, 9225, 9226, 9227],
    matched_files=test_files,
    include_baseline=False,
    baseline_file='data/asus_locations.json',
    mode='manual',
    headless=False,
    log_ts='test_progress'
)

print(f"\n✓ 測試完成，共 {len(data)} 筆")
print(f"✓ 查看 logs: run_test_progress_port9222.txt 等")
