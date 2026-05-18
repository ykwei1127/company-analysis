"""
Glassdoor 爬蟲工具 - 整合版
支援兩種模式：
1. 自動模式：自動啟動 Chrome（可能遇到反爬蟲）
2. 手動模式：連接到已登入的 Chrome（推薦）
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class GlassdoorScraper:
    def __init__(self, mode='manual', headless=False, chrome_debugger_port=9222, _log_fn=None):
        """
        初始化 Glassdoor 爬蟲
        
        Args:
            mode: 'manual' 或 'auto'
                - 'manual': 連接到已登入的 Chrome（推薦，避免反爬蟲）
                - 'auto': 自動啟動新的 Chrome（可能遇到人機驗證）
            headless: 僅在 auto 模式下有效，是否隱藏瀏覽器
            chrome_debugger_port: 僅在 manual 模式下有效，Chrome 調試端口
            _log_fn: 可選的 logging 函式 (msg, end) → 供平行模式各 port 獨立記錄
        """
        self.mode = mode
        self._log = _log_fn if _log_fn else lambda msg='', end='\n': print(msg, end=end)
        chrome_options = Options()
        
        if mode == 'manual':
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{chrome_debugger_port}")
            self._log(f"📌 使用手動模式：連接到端口 {chrome_debugger_port} 的 Chrome")
        else:
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            self._log(f"📌 使用自動模式：啟動新的 Chrome（headless={headless}）")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        
    def extract_rating_data(self, url, company_name):
        """
        從 Glassdoor 頁面提取評分數據
        
        Args:
            url: Glassdoor 評論頁面 URL
            company_name: 公司名稱（用於標識）
            
        Returns:
            dict: 包含各項評分的字典
        """
        self._log(f"正在抓取: {company_name}")
        self._log(f"URL: {url}")
        _t0 = time.time()
        
        try:
            self.driver.get(url)

            # 等 Overall 評分出現（最多 8 秒），取代固定 sleep(5)
            data = {
                'Company': company_name,
                'Overall': None,
                'Recommend': None,
                'CEO Approval': None,
                'Total Reviews': None,
                'Diversity & Inclusion': None,
                'Work/Life Balance': None,
                'Compensation and Benefits': None,
                'Culture & Values': None,
                'Career Opportunities': None,
                'Senior Management': None
            }

            # 提取整體評分
            try:
                overall_elem = WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'p[data-size-variant="lg"]'))
                )
                overall_rating = overall_elem.text
                data['Overall'] = float(overall_rating)
                self._log(f"  ✓ Overall: {overall_rating}")
            except Exception as e:
                self._log(f"  ⚠ 無法找到整體評分")

            # 滾動頁面以觸發動態載入
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)
            
            # 提取推薦比例
            try:
                recommend_elem = self.driver.find_element(By.CSS_SELECTOR, 'p[data-test="recommendToFriend"]')
                recommend_text = recommend_elem.text
                match = re.search(r'(\d+)%', recommend_text)
                if match:
                    data['Recommend'] = f"{match.group(1)}%"
                    self._log(f"  ✓ Recommend: {data['Recommend']}")
            except Exception as e:
                self._log(f"  ⚠ 無法找到推薦比例")
            
            # 提取 CEO 支持率
            try:
                ceo_elem = self.driver.find_element(By.CSS_SELECTOR, 'p[class*="ceoApproval"]')
                ceo_match = re.search(r'(\d+)%', ceo_elem.text)
                if ceo_match:
                    data['CEO Approval'] = f"{ceo_match.group(1)}%"
                    self._log(f"  ✓ CEO Approval: {data['CEO Approval']}")
            except Exception:
                self._log(f"  ⚠ 無法找到 CEO 支持率")

            # 提取評論總數
            try:
                review_count_elem = self.driver.find_element(By.CSS_SELECTOR, '.ReviewOverview_count__xexV9')
                review_text = review_count_elem.get_attribute('textContent')
                match = re.search(r'([\d,]+)', review_text)
                if match:
                    data['Total Reviews'] = match.group(1)
                    self._log(f"  ✓ Total Reviews: {data['Total Reviews']}")
            except Exception as e:
                self._log(f"  ⚠ 無法找到評論總數")
            
            # 提取各項評分
            try:
                rating_items = self.driver.find_elements(By.CSS_SELECTOR, '.RatingsByCategory_ratingItem__4EMZd')
                
                for item in rating_items:
                    try:
                        rating_value = item.find_element(By.CSS_SELECTOR, '.RatingsByCategory_rating__T0v8N').text
                        category_label = item.find_element(By.CSS_SELECTOR, '.RatingsByCategory_ratingLabel__o3Me9').text
                        
                        if 'Diversity' in category_label or 'inclusion' in category_label:
                            data['Diversity & Inclusion'] = float(rating_value)
                            self._log(f"  ✓ Diversity & Inclusion: {rating_value}")
                        elif 'Work/Life' in category_label or 'Work-Life' in category_label:
                            data['Work/Life Balance'] = float(rating_value)
                            self._log(f"  ✓ Work/Life Balance: {rating_value}")
                        elif 'Compensation' in category_label or 'benefits' in category_label:
                            data['Compensation and Benefits'] = float(rating_value)
                            self._log(f"  ✓ Compensation and Benefits: {rating_value}")
                        elif 'Culture' in category_label or 'values' in category_label:
                            data['Culture & Values'] = float(rating_value)
                            self._log(f"  ✓ Culture & Values: {rating_value}")
                        elif 'Career' in category_label or 'opportunities' in category_label:
                            data['Career Opportunities'] = float(rating_value)
                            self._log(f"  ✓ Career Opportunities: {rating_value}")
                        elif 'Senior' in category_label or 'management' in category_label:
                            data['Senior Management'] = float(rating_value)
                            self._log(f"  ✓ Senior Management: {rating_value}")
                    except Exception as e:
                        continue
                        
            except Exception as e:
                self._log(f"  ⚠ 提取評分時發生錯誤: {str(e)}")
            
            # 檢查缺失的數據（排除由呼叫端填入的 metadata 欄位）
            _meta_cols = {'Baseline Location', 'Actual City', 'Country'}
            missing_fields = [k for k, v in data.items() if k not in _meta_cols and k != 'Company' and v is None]
            if missing_fields:
                self._log(f"  ⚠ 缺失欄位: {', '.join(missing_fields)}")
            
            self._log(f"✓ 成功抓取 {company_name} ({time.time() - _t0:.1f}s)")
            return data
            
        except Exception as e:
            self._log(f"✗ 抓取 {company_name} 時發生錯誤: {str(e)} ({time.time() - _t0:.1f}s)")
            return None
    
    def scrape_multiple_companies(self, company_urls):
        """
        抓取多個公司的數據
        
        Args:
            company_urls: 字典，格式為 {公司名稱: URL}
            
        Returns:
            list: 包含所有公司數據的列表
        """
        all_data = []
        
        for company_name, url in company_urls.items():
            data = self.extract_rating_data(url, company_name)
            if data:
                all_data.append(data)
            time.sleep(3)
            self._log()
        
        return all_data

    def scrape_from_matched_json(self, json_files, _progress_fn=None):
        """
        從 company_finder.py 產生的 *_matched.json 抓取評分數據。
        保留 baseline_location 和 matched_city，讓 Excel 顯示正確。

        Args:
            json_files: list of str，matched json 路徑
            _progress_fn: callable(entry_name)，每筆 entry 完成後回報進度

        Returns:
            list of dict
        """
        import json
        all_data = []
        total_start = time.time()
        count = 0

        for json_file in json_files:
            with open(json_file, encoding='utf-8') as f:
                entries = json.load(f)

            for entry in entries:
                if entry['status'] != 'found' or not entry.get('url'):
                    continue
                company = entry['company']
                baseline_loc = entry['baseline_location']
                actual_city = entry.get('matched_city') or baseline_loc
                url = entry['url']

                country = entry.get('baseline_country')
                display_name = f"{company} - {baseline_loc}"
                data = self.extract_rating_data(url, display_name)
                sleep_sec = 0.5
                if data:
                    data['Baseline Location'] = baseline_loc
                    data['Actual City'] = actual_city
                    data['Country'] = country
                    data['Review URL'] = url
                    all_data.append(data)
                    # 成功且有關鍵欄位才等較久，否則短等待
                    if data.get('Overall') is not None:
                        sleep_sec = 1.5
                count += 1
                # 回報進度
                if _progress_fn:
                    _progress_fn(display_name)
                time.sleep(sleep_sec)
                self._log()

        total = time.time() - total_start
        if count:
            self._log(f"⏱ 總計 {count} 筆，耗時 {total:.0f}s，平均 {total/count:.1f}s/筆")
        return all_data
    
    def scrape_from_baseline_json(self, json_file, company_name='ASUS', location_filter=None, _progress_fn=None):
        """
        讀取 explore 模式產生的 *_locations.json（如 asus_locations.json）並抓取評分。

        Args:
            json_file: str，locations json 路徑
            company_name: str，公司名稱
            location_filter: str or None，若指定則只處理該地區
            _progress_fn: callable(entry_name)，每筆 entry 完成後回報進度

        Returns:
            list of dict
        """
        import json
        all_data = []

        with open(json_file, encoding='utf-8') as f:
            entries = json.load(f)

        for entry in entries:
            if entry.get('status') != 'found' or not entry.get('url'):
                continue
            baseline_loc = entry['location']
            if location_filter and baseline_loc != location_filter:
                continue
            country = entry.get('country')
            url = entry['url']

            display_name = f"{company_name} - {baseline_loc}"
            data = self.extract_rating_data(url, display_name)
            sleep_sec = 0.5
            if data:
                data['Baseline Location'] = baseline_loc
                data['Actual City'] = baseline_loc
                data['Country'] = country
                data['Review URL'] = url
                all_data.append(data)
                if data.get('Overall') is not None:
                    sleep_sec = 1.5
            # 回報進度
            if _progress_fn:
                _progress_fn(display_name)
            time.sleep(sleep_sec)
            self._log()

        return all_data

    def save_to_excel(self, data, output_file='glassdoor_ratings.xlsx'):
        """
        將數據保存為 Excel 文件
        
        Args:
            data: 數據列表
            output_file: 輸出文件名
        """
        if not data:
            print("沒有數據可以保存")
            return
        
        df = pd.DataFrame(data)
        
        # 調整列順序（相容有無 Location 欄位）
        base_cols = ['Company', 'Baseline Location', 'Country', 'Actual City', 'Review URL', 'Overall', 'Recommend',
                     'CEO Approval', 'Total Reviews', 'Diversity & Inclusion', 'Work/Life Balance',
                     'Compensation and Benefits', 'Culture & Values',
                     'Career Opportunities', 'Senior Management']
        columns_order = [c for c in base_cols if c in df.columns]
        df = df[columns_order]
        
        # 保存為 Excel
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"\n✓ 數據已保存至: {output_file}")  # save_to_excel 由主 thread 呼叫，用 print
        
        # 美化 Excel
        from openpyxl import load_workbook
        from openpyxl.styles import Font, Alignment, PatternFill
        
        wb = load_workbook(output_file)
        ws = wb.active
        
        # 設置標題樣式
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # 設置列寬
        col_widths = {'A': 30, 'B': 22, 'C': 22, 'D': 10, 'E': 12,
                      'F': 14, 'G': 20, 'H': 18, 'I': 24, 'J': 16,
                      'K': 22, 'L': 18}
        for col, width in col_widths.items():
            ws.column_dimensions[col].width = width
        
        # 居中對齊數據
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                cell.alignment = Alignment(horizontal='center', vertical='center')
        
        wb.save(output_file)
        print(f"✓ Excel 格式已美化")

        # 同步輸出 CSV
        csv_file = os.path.splitext(output_file)[0] + '.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"✓ CSV 已保存至: {csv_file}")  # save_to_excel 由主 thread 呼叫，用 print
    
    def close(self):
        """關閉瀏覽器"""
        if self.mode == 'auto':
            self.driver.quit()
        else:
            # 手動模式不關閉瀏覽器
            pass


def _worker(port, tasks, mode, headless, log_path=None, _progress=None):
    """
    單一執行緒的工作函式，負責一個 Chrome port 的所有任務。
    輸出收集到獨立 buffer，不修改全域 sys.stdout，避免多 thread 交錯。

    Args:
        port: Chrome debug port
        tasks: list of dict，每筆含 type('baseline'|'matched'), 以及對應參數
        mode: scraper mode
        headless: bool
        log_path: 此 port 專屬的 log 路徑，None 則不寫檔
        _progress: dict，用於回報進度給主執行緒

    Returns:
        list of dict
    """
    import io
    import threading

    buf = io.StringIO()  # 仍保留一份給最後合併主 log 用
    _lock = threading.Lock()
    _log_file = None

    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        _log_file = open(log_path, 'w', encoding='utf-8')

    def _log(msg='', end='\n'):
        s = str(msg) + end
        with _lock:
            buf.write(s)
            if _log_file:
                _log_file.write(s)
                _log_file.flush()  # 即時 flush 到磁碟

    scraper = GlassdoorScraper(mode=mode, headless=headless,
                               chrome_debugger_port=port, _log_fn=_log)
    results = []
    try:
        total = len(tasks)
        for i, task in enumerate(tasks):
            # 更新進度
            task_name = task.get('company_name', task.get('file', 'unknown'))
            if task.get('location_filter'):
                task_name += f" [{task['location_filter']}]"
            # 定義 progress callback，每筆 entry 完成後更新 _progress
            def _progress_fn(entry_name):
                if _progress is not None:
                    with threading.Lock():
                        _progress[port]['completed'] += 1
                        _progress[port]['current'] = entry_name

            if task['type'] == 'baseline':
                results += scraper.scrape_from_baseline_json(
                    task['file'], task['company_name'],
                    location_filter=task.get('location_filter'),
                    _progress_fn=_progress_fn
                )
            elif task['type'] == 'matched':
                results += scraper.scrape_from_matched_json([task['file']], _progress_fn=_progress_fn)

    finally:
        scraper.close()
        if _log_file:
            _log_file.close()
        # 標記完成
        if _progress is not None:
            with threading.Lock():
                _progress[port]['finished'] = True
    return results


def parallel_scrape(ports, matched_files, include_baseline, baseline_file,
                    mode='manual', headless=False, log_ts=None):
    """
    將任務平均分配給多個 Chrome port 並平行執行。
    每個 port 獨立寫 log，完成後合並到主 log。

    Returns:
        list of dict
    """
    import threading

    tasks_all = []

    if include_baseline and os.path.exists(baseline_file):
        # 把 ASUS baseline 拆成每個地區一個 task，分散分配避免照成瓶頃
        with open(baseline_file, encoding='utf-8') as _f:
            _entries = json.load(_f)
        for _e in _entries:
            if _e.get('status') == 'found' and _e.get('url'):
                tasks_all.append({
                    'type': 'baseline',
                    'file': baseline_file,
                    'company_name': 'ASUS',
                    'location_filter': _e['location'],
                })

    for f in matched_files:
        tasks_all.append({'type': 'matched', 'file': f})

    if not tasks_all:
        return []

    # 平均分配到各 port
    buckets = [[] for _ in ports]
    for i, task in enumerate(tasks_all):
        buckets[i % len(ports)].append(task)

    ts = log_ts or ''
    port_logs = {port: f'logs/run_{ts}_port{port}.txt' for port in ports}

    # 進度追蹤（空 bucket 直接標記完成）
    _progress = {}
    for port, bucket in zip(ports, buckets):
        if bucket:
            _progress[port] = {'completed': 0, 'current': 'init', 'finished': False}
        else:
            _progress[port] = {'completed': 0, 'current': '-', 'finished': True}

    # 總任務數（先不精確計算，用一個預估值或動態更新）
    total_tasks = len(tasks_all) * 10  # 粗略估計每個 task 平均 10 筆 entries

    total_start = time.time()
    all_data = []
    port_counts = {}

    _last_printed = 0

    def _print_progress(force=False):
        """Print simple text progress for dashboard parsing."""
        nonlocal _last_printed
        total_completed = sum(p['completed'] for p in _progress.values())
        if total_completed == _last_printed and not force:
            return
        _last_printed = total_completed
        parts = []
        for port in sorted(_progress.keys()):
            p = _progress[port]
            if p['finished']:
                parts.append(f"P{port}:OK({p['completed']})")
            else:
                parts.append(f"P{port}:{p['completed']}")
        print(f"[PROGRESS] {total_completed}/{total_tasks} | {' | '.join(parts)}", flush=True)

    executor = ThreadPoolExecutor(max_workers=len(ports))
    futures = {
        executor.submit(_worker, port, bucket, mode, headless, port_logs[port], _progress): port
        for port, bucket in zip(ports, buckets) if bucket
    }

    try:
        while futures:
            done_futures = []
            for f in list(futures):
                if f.done():
                    port = futures[f]
                    try:
                        data = f.result()
                        all_data += data
                        port_counts[port] = len(data)
                        print(f"[DONE] Port {port} completed {len(data)} entries  log: {port_logs[port]}", flush=True)
                    except Exception as e:
                        print(f"[ERROR] Port {port} error: {e}", flush=True)
                    done_futures.append(f)
                    _progress[port]['finished'] = True

            for f in done_futures:
                del futures[f]

            _print_progress()

            if futures:
                time.sleep(3)

    except KeyboardInterrupt:
        print("\n[WARN] Ctrl+C received, stopping workers...", flush=True)
        for f in futures:
            f.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise

    elapsed = time.time() - total_start
    print(f"\n[DONE] Parallel scraping completed in {elapsed:.0f}s, {len(all_data)} entries total", flush=True)

    # 將各 port log 合並追加到主 log
    import sys as _sys
    main_log = getattr(getattr(_sys.stdout, '_file', None), 'name', None)
    if main_log:
        try:
            with open(main_log, 'a', encoding='utf-8') as mf:
                mf.write(f"\n{'='*60}\n")
                mf.write(f"Per-Port Detailed Logs\n")
                mf.write(f"{'='*60}\n")
                for port in ports:
                    plog = port_logs[port]
                    if os.path.exists(plog):
                        mf.write(f"\n--- port {port} ({port_counts.get(port, 0)} 筆) ---\n")
                        with open(plog, encoding='utf-8') as pf:
                            mf.write(pf.read())
        except Exception:
            pass

    return all_data


class TeeLogger:
    """將 stdout 同時輸出到終端和檔案"""
    def __init__(self, filepath):
        import sys
        self._terminal = sys.stdout
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self._file = open(filepath, 'w', encoding='utf-8')
        import sys as _sys
        _sys.stdout = self

    def write(self, message):
        self._terminal.write(message)
        self._file.write(message)

    def flush(self):
        self._terminal.flush()
        self._file.flush()

    def restore(self):
        import sys
        sys.stdout = self._terminal
        self._file.close()


def save_run_report(data, elapsed, log_txt_path, json_path):
    """產出 JSON 摘要報告"""
    from datetime import datetime
    import collections

    company_stats = collections.defaultdict(lambda: {'success': 0, 'failed': 0, 'missing': []})
    for row in data:
        company = row.get('Company', 'Unknown').split(' - ')[0]
        company_stats[company]['success'] += 1
        missing = [k for k, v in row.items()
                   if v is None and k not in ('Company', 'Baseline Location', 'Actual City', 'Country')]
        if missing:
            company_stats[company]['missing'].append({'location': row.get('Baseline Location'), 'fields': missing})

    report = {
        'run_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'elapsed_seconds': round(elapsed, 1),
        'elapsed_human': f"{int(elapsed//60)}m {int(elapsed%60)}s",
        'total_rows': len(data),
        'log_file': log_txt_path,
        'companies': {k: dict(v) for k, v in company_stats.items()},
    }

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON 摘要已保存至: {json_path}")


def load_config():
    """載入配置文件"""
    try:
        # 嘗試導入 config.py
        import config
        return config
    except ImportError:
        # 如果沒有 config.py，嘗試 config_example.py
        try:
            import config_example as config
            print("⚠ 使用 config_example.py，建議複製為 config.py 並修改")
            return config
        except ImportError:
            print("✗ 找不到配置文件")
            return None


def main():
    import glob
    from datetime import datetime
    _main_start = time.time()
    _ts = datetime.now().strftime('%Y%m%d_%H%M')
    _log_txt = f'logs/run_{_ts}.txt'
    _log_json = f'logs/run_{_ts}.json'
    _tee = TeeLogger(_log_txt)
    print(f"📋 Log 記錄至：{_log_txt}")

    # 載入配置
    config = load_config()
    scraper_config = getattr(config, 'SCRAPER_CONFIG', {}) if config else {}
    output_config = getattr(config, 'OUTPUT_CONFIG', {}) if config else {}
    mode = scraper_config.get('mode', 'manual')
    headless = scraper_config.get('headless', False)
    _base_output = output_config.get('filename', 'data/glassdoor_ratings.xlsx')
    _stem, _ext = os.path.splitext(_base_output)
    output_file = f"{_stem}_{_ts}{_ext}"

    # 優先使用 data/*_matched.json（company_finder 產生的結果）
    matched_files = sorted(glob.glob('data/*_matched.json'))

    if mode == 'manual':
        print("\n" + "="*60)
        print("手動模式 - 使用已登入的 Chrome")
        print("="*60)
        print("\n請確認：")
        print("1. 已執行 啟動Chrome.bat")
        print("2. 已在 Chrome 中登入 Glassdoor")
        print("\n如果還沒準備好，請按 Ctrl+C 取消")
        print("準備好後按 Enter 繼續...")
        input()

    include_baseline = getattr(config, 'INCLUDE_BASELINE', False) if config else False
    baseline_file = 'data/asus_locations.json'
    parallel_ports = getattr(config, 'PARALLEL_PORTS', []) if config else []

    # 單一 port 或空清單 → 單一模式；多個 port → 平行模式
    use_parallel = len(parallel_ports) > 1

    try:
        if use_parallel:
            print(f"\n⚡ 平行模式：使用 {len(parallel_ports)} 個 Chrome（ports: {parallel_ports}）")
            print("請確認每個 port 的 Chrome 都已登入 Glassdoor\n")
            data = parallel_scrape(
                ports=parallel_ports,
                matched_files=matched_files,
                include_baseline=include_baseline,
                baseline_file=baseline_file,
                mode=mode,
                headless=headless,
                log_ts=_ts,
            )
        else:
            port = parallel_ports[0] if parallel_ports else 9222
            scraper = GlassdoorScraper(mode=mode, headless=headless, chrome_debugger_port=port)
            data = []

            if include_baseline and os.path.exists(baseline_file):
                print(f"\n[INCLUDE_BASELINE=True] 抓取基準公司 ASUS：{baseline_file}\n")
                data += scraper.scrape_from_baseline_json(baseline_file, company_name='ASUS')

            if matched_files:
                print(f"\n找到 matched JSON：{matched_files}")
                print(f"開始從 matched JSON 抓取數據...\n")
                data += scraper.scrape_from_matched_json(matched_files)
            elif not include_baseline:
                if config and hasattr(config, 'COMPANY_URLS'):
                    companies = config.COMPANY_URLS
                    print(f"\n開始抓取 {len(companies)} 個公司的數據...\n")
                    data += scraper.scrape_multiple_companies(companies)
                else:
                    print("找不到 matched JSON 也沒有 config.py，請先執行 company_finder.py match")
                    return

            scraper.close()

        if data:
            # save_to_excel 不需要 driver，建一個不連 Chrome 的輕量實例
            saver = object.__new__(GlassdoorScraper)
            saver.mode = mode
            saver.save_to_excel(data, output_file)
            print(f"\n✓ 完成！共抓取 {len(data)} 筆數據")
        else:
            print("\n✗ 沒有成功抓取任何數據")

    except Exception as e:
        import traceback
        print(f"\n✗ 發生錯誤: {e}")
        traceback.print_exc()
        if mode == 'manual':
            print("\n請確認 Chrome 是否已用 --remote-debugging-port=9222 啟動")

    finally:
        elapsed = time.time() - _main_start
        print(f"\n⏱ 總執行時間：{elapsed//60:.0f}m {elapsed%60:.0f}s")
        try:
            save_run_report(data if 'data' in dir() else [], elapsed, _log_txt, _log_json)
        except Exception:
            pass
        _tee.restore()
        print(f"📋 Log 已儲存：{_log_txt}")


if __name__ == '__main__':
    main()
