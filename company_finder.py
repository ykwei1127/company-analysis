"""
Glassdoor 跨公司地區比較工具

兩種模式：
1. 首次探索（explore）：從公司的 Office Locations 頁抓取所有地區 URL
2. 比對模式（match）：以基準地區清單（如 ASUS 的 22 個地區）對新公司搜尋對應 URL

使用方式：
    # 首次探索（建立基準，僅需做一次）
    python company_finder.py explore

    # 對新公司比對基準地區
    python company_finder.py match

前置條件：
    已執行 啟動Chrome.bat 並在 Chrome 中登入 Glassdoor
"""

import time
import re
import json
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options


# ============================================================
# 全域設定
# ============================================================
CHROME_DEBUG_PORT = 9222
BASELINE_FILE = 'data/asus_locations.json'  # 基準地區清單

# 首次探索用（explore 模式）
EXPLORE_CONFIG = {
    'name': 'ASUS',
    'company_id': 'E40093',
    'locations_url': 'https://www.glassdoor.com/Location/All-ASUS-Office-Locations-E40093.htm',
}

# 比對模式：只需填入公司名稱，ID 和 URL 會自動從 Glassdoor 搜尋
COMPANIES_TO_MATCH = [
    'TSMC',
]
# ============================================================


class CompanyFinder:
    def __init__(self, chrome_debugger_port=9222):
        chrome_options = Options()
        chrome_options.add_experimental_option(
            "debuggerAddress", f"127.0.0.1:{chrome_debugger_port}"
        )
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        print(f"已連接到 Chrome (port {chrome_debugger_port})")

    # ----------------------------------------------------------------
    # 首次探索模式
    # ----------------------------------------------------------------
    def explore_all_locations(self, company_config):
        """從公司 Office Locations 頁抓取所有地區 URL（首次建立基準用）"""
        url = company_config['locations_url']
        numeric_id = re.sub(r'[^\d]', '', company_config['company_id'])
        company_name = company_config['name']

        print(f"\n正在載入 Office Locations 頁面：{url}")
        self.driver.get(url)
        time.sleep(5)
        self._scroll_to_bottom()
        print("頁面載入完成，開始收集城市連結...")

        city_links = self._collect_city_links(numeric_id)
        print(f"找到 {len(city_links)} 個城市辦公室")

        results = []
        for i, (city_name, city_info) in enumerate(city_links.items(), 1):
            city_loc_url = city_info['url']
            list_rating = city_info['list_rating']
            address = city_info['address']
            print(f"\n[{i}/{len(city_links)}] {city_name} (列表評分: {list_rating})")
            review_url, review_count, page_heading = self._find_review_url_from_city_page(city_loc_url, numeric_id)

            country = self._extract_country(page_heading, address)

            if review_url:
                print(f"  ✅ 國家: {country}  URL: {review_url}")
                results.append({
                    'location': city_name,
                    'country': country,
                    'page_heading': page_heading,
                    'heading_is_generic': page_heading in (None, company_name, 'ASUS'),
                    'list_rating': list_rating,
                    'address': address,
                    'url': review_url,
                    'reviews_count': review_count,
                    'status': 'found',
                })
            else:
                print(f"  ⚠️  無 Review URL  國家: {country}")
                results.append({
                    'location': city_name,
                    'country': country,
                    'page_heading': page_heading,
                    'heading_is_generic': True,
                    'list_rating': list_rating,
                    'address': address,
                    'url': None,
                    'reviews_count': None,
                    'status': 'no_review_url',
                })
            time.sleep(2)

        return results

    # ----------------------------------------------------------------
    # 比對模式
    # ----------------------------------------------------------------
    def match_against_baseline(self, company_config, baseline_locations):
        """
        以基準地區清單對新公司搜尋對應 review URL。

        策略：
        1. 載入新公司的 Office Locations 頁，收集所有城市連結
        2. 對每個基準地區，用國家名比對新公司的城市
        3. 找到對應城市後進入其 Location 頁取 review URL
        4. 找不到則標記 status='not_in_company'

        Returns:
            list of dict，每筆對應一個基準地區
        """
        numeric_id = re.sub(r'[^\d]', '', company_config['company_id'])
        company_name = company_config['name']
        url = company_config['locations_url']

        print(f"\n正在載入 {company_name} Office Locations 頁面：{url}")
        self.driver.get(url)
        time.sleep(5)
        self._scroll_to_bottom()
        print("頁面載入完成，開始收集城市連結...")

        city_links = self._collect_city_links(numeric_id)
        print(f"找到 {len(city_links)} 個城市辦公室")

        # 建立 country → city 對照表（一個國家可能有多個城市，取第一個）
        country_to_city = {}
        for city_name, city_info in city_links.items():
            address = city_info['address'] or ''
            country = self._extract_country(None, address)
            if country and country not in country_to_city:
                country_to_city[country] = (city_name, city_info)

        print(f"可比對國家：{sorted(country_to_city.keys())}")

        global_review_url = company_config.get('global_review_url')
        results = []
        baseline_found = [loc for loc in baseline_locations if loc['status'] == 'found']

        for i, baseline in enumerate(baseline_found, 1):
            ref_country = baseline['country']
            ref_location = baseline['location']
            print(f"\n[{i}/{len(baseline_found)}] 基準地區：{ref_location} ({ref_country})")

            # Global 基準地區：直接填入 global review URL
            if ref_location == 'Global':
                if global_review_url:
                    print(f"  ✅ Global review URL：{global_review_url}")
                    results.append({
                        'baseline_location': 'Global',
                        'baseline_country': None,
                        'company': company_name,
                        'matched_city': 'Global',
                        'url': global_review_url,
                        'reviews_count': None,
                        'status': 'found',
                    })
                else:
                    results.append({
                        'baseline_location': 'Global',
                        'baseline_country': None,
                        'company': company_name,
                        'matched_city': None,
                        'url': None,
                        'reviews_count': None,
                        'status': 'no_review_url',
                    })
                continue

            # 在新公司的城市裡找相同國家
            matched_city = None
            matched_info = None
            for country, (city_name, city_info) in country_to_city.items():
                if self._country_match(ref_country, country):
                    matched_city = city_name
                    matched_info = city_info
                    break

            if not matched_city:
                print(f"  ➖ {company_name} 無此國家辦公室")
                results.append({
                    'baseline_location': ref_location,
                    'baseline_country': ref_country,
                    'company': company_name,
                    'matched_city': None,
                    'url': None,
                    'reviews_count': None,
                    'status': 'not_in_company',
                })
                continue

            print(f"  📍 找到對應城市：{matched_city}")
            review_url, review_count, page_heading = self._find_review_url_from_city_page(
                matched_info['url'], numeric_id
            )

            if review_url:
                print(f"  ✅ Review URL：{review_url}")
                results.append({
                    'baseline_location': ref_location,
                    'baseline_country': ref_country,
                    'company': company_name,
                    'matched_city': matched_city,
                    'url': review_url,
                    'reviews_count': review_count,
                    'status': 'found',
                })
            else:
                print(f"  ⚠️  城市存在但無 Review URL")
                results.append({
                    'baseline_location': ref_location,
                    'baseline_country': ref_country,
                    'company': company_name,
                    'matched_city': matched_city,
                    'url': None,
                    'reviews_count': None,
                    'status': 'no_review_url',
                })
            time.sleep(2)

        return results

    # ----------------------------------------------------------------
    # 共用工具方法
    # ----------------------------------------------------------------
    def _scroll_to_bottom(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _collect_city_links(self, numeric_id):
        city_links = {}
        all_links = self.driver.find_elements(By.TAG_NAME, 'a')
        for link in all_links:
            try:
                href = link.get_attribute('href') or ''
                text = link.text.strip()
                if not href or not text:
                    continue
                if '/Location/All-' not in href:
                    continue
                if numeric_id not in href:
                    continue
                if re.search(rf'All-[^/]+-Office-Locations-E', href) and \
                   not re.search(rf'All-[^/]+-[^/]+-Office-Locations-E', href):
                    continue
                clean_href = href.split('?')[0]
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                city_name = lines[0] if lines else ''
                rating_match = re.search(r'(\d\.\d)', text)
                list_rating = float(rating_match.group(1)) if rating_match else None
                address = lines[-1] if len(lines) > 1 else None
                if city_name and clean_href not in [v['url'] for v in city_links.values()]:
                    city_links[city_name] = {
                        'url': clean_href,
                        'list_rating': list_rating,
                        'address': address,
                    }
            except Exception:
                continue
        return city_links

    def _find_review_url_from_city_page(self, city_loc_url, numeric_id):
        self.driver.get(city_loc_url)
        time.sleep(3)

        page_heading = None
        for sel in ['h1', 'h2', '[class*="heading"]', '[class*="Heading"]']:
            try:
                elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for elem in elems:
                    t = elem.text.strip()
                    if t and 3 < len(t) < 80:
                        page_heading = t
                        break
                if page_heading:
                    break
            except Exception:
                continue

        all_links = self.driver.find_elements(By.TAG_NAME, 'a')
        for link in all_links:
            try:
                href = link.get_attribute('href') or ''
                text = link.text.strip()
                if not href:
                    continue
                if '/Reviews/' not in href:
                    continue
                if numeric_id not in href:
                    continue
                if not any(p in href for p in ['_IL.', '_IC', '_IN', '_IM']):
                    continue
                clean_href = href.split('?')[0]
                count_match = re.search(r'(\d[\d,]*)\s*review', text, re.IGNORECASE)
                count = int(count_match.group(1).replace(',', '')) if count_match else None
                return clean_href, count, page_heading
            except Exception:
                continue
        return None, None, page_heading

    def _extract_country(self, page_heading, address):
        """從 heading 括號或 address 最後一段取國家名"""
        if page_heading:
            m = re.search(r'\(([^)]+)\)', page_heading)
            if m:
                return m.group(1).strip()
        if address:
            parts = [p.strip() for p in address.split(',')]
            if len(parts) >= 2:
                return parts[-1].strip()
        return None

    def _country_match(self, country_a, country_b):
        """模糊比對國家名（不區分大小寫，允許部分匹配）"""
        if not country_a or not country_b:
            return False
        a = country_a.lower().strip()
        b = country_b.lower().strip()
        return a == b or a in b or b in a

    def save_results(self, results, company_name, output_file=None):
        if output_file is None:
            safe_name = company_name.lower().replace(' ', '_')
            output_file = f"data/{safe_name}_locations.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n結果已儲存至：{output_file}")

    def print_match_results(self, results, company_name):
        found = [r for r in results if r['status'] == 'found']
        no_review = [r for r in results if r['status'] == 'no_review_url']
        not_in = [r for r in results if r['status'] == 'not_in_company']

        print(f"\n{'='*60}")
        print(f"{company_name} vs 基準地區比對結果")
        print(f"{'='*60}")
        print(f"✅ 找到 Review URL：{len(found)}/{len(results)} 個")
        for r in found:
            print(f"  {r['baseline_location']:<25} ({r['baseline_country']}) → {r['matched_city']}")
        if no_review:
            print(f"\n⚠️  有辦公室但無 Review URL：{len(no_review)} 個")
            for r in no_review:
                print(f"  {r['baseline_location']:<25} ({r['baseline_country']}) → {r['matched_city']}")
        if not_in:
            print(f"\n➖ 無此國家辦公室：{len(not_in)} 個")
            for r in not_in:
                print(f"  {r['baseline_location']:<25} ({r['baseline_country']})")

    def search_company(self, company_name):
        """
        在 Glassdoor 搜尋公司名稱，自動取得 company_id 和 locations_url。
        返回 dict 或 None（找不到時）。
        """
        search_url = f"https://www.glassdoor.com/Search/results.htm?keyword={company_name.replace(' ', '+')}"
        print(f"\n搜尋：{search_url}")
        self.driver.get(search_url)
        time.sleep(4)

        all_links = self.driver.find_elements(By.TAG_NAME, 'a')
        for link in all_links:
            try:
                href = link.get_attribute('href') or ''
                # 目標：/Overview/ 或 /Reviews/ 頁面，含 E{數字}
                m = re.search(r'[-_]E(\d+)(?:\.htm|$|[,.])', href)
                if not m:
                    continue
                # 確認是公司頁，排除 job/salary 等
                if not any(p in href for p in ['/Overview/', '/Reviews/', '/Location/']):
                    continue
                numeric_id = m.group(1)
                # 從 href 取公司 slug（Overview URL 格式最乾淨）
                slug_match = re.search(r'/(?:Overview|Reviews|Location)/([^/]+)-(?:Overview|Reviews|Office-Locations)-E\d+', href)
                if slug_match:
                    slug = slug_match.group(1)
                else:
                    slug = company_name.replace(' ', '-')

                company_id = f"E{numeric_id}"
                locations_url = f"https://www.glassdoor.com/Location/All-{slug}-Office-Locations-{company_id}.htm"
                global_review_url = f"https://www.glassdoor.com/Reviews/{slug}-Reviews-{company_id}.htm"
                print(f"  找到：{company_name} → ID={company_id}, slug={slug}")
                return {
                    'name': company_name,
                    'company_id': company_id,
                    'locations_url': locations_url,
                    'global_review_url': global_review_url,
                }
            except Exception:
                continue

        # 備用：嘗試直接從 Overview 頁面抓
        print(f"  搜尋結果未找到，嘗試備用方式...")
        fallback_url = f"https://www.glassdoor.com/Search/results.htm?keyword={company_name.replace(' ', '+')}&type=EMPLOYER"
        self.driver.get(fallback_url)
        time.sleep(4)
        all_links = self.driver.find_elements(By.TAG_NAME, 'a')
        for link in all_links:
            try:
                href = link.get_attribute('href') or ''
                m = re.search(r'[-_]E(\d+)(?:\.htm|$|[,.])', href)
                if not m:
                    continue
                if '/Overview/' not in href and '/Reviews/' not in href:
                    continue
                numeric_id = m.group(1)
                slug_match = re.search(r'/(?:Overview|Reviews)/([^/]+)-(?:Overview|Reviews)-E\d+', href)
                slug = slug_match.group(1) if slug_match else company_name.replace(' ', '-')
                company_id = f"E{numeric_id}"
                locations_url = f"https://www.glassdoor.com/Location/All-{slug}-Office-Locations-{company_id}.htm"
                global_review_url = f"https://www.glassdoor.com/Reviews/{slug}-Reviews-{company_id}.htm"
                print(f"  備用找到：{company_name} → ID={company_id}")
                return {
                    'name': company_name,
                    'company_id': company_id,
                    'locations_url': locations_url,
                    'global_review_url': global_review_url,
                }
            except Exception:
                continue

        print(f"  ❌ 無法自動找到 {company_name} 的 Glassdoor ID")
        return None

    def close(self):
        pass


# ----------------------------------------------------------------
# 主程式
# ----------------------------------------------------------------
def run_explore():
    print("=" * 60)
    print("模式：首次探索（建立基準地區清單）")
    print("=" * 60)
    finder = CompanyFinder(CHROME_DEBUG_PORT)
    try:
        results = finder.explore_all_locations(EXPLORE_CONFIG)
        finder.save_results(results, EXPLORE_CONFIG['name'])
        print(f"\n完成！共 {len(results)} 個地區")
    except Exception as e:
        print(f"\n錯誤：{e}")
        import traceback; traceback.print_exc()
    finally:
        finder.close()


def run_match():
    print("=" * 60)
    print("模式：比對新公司 vs 基準地區")
    print("=" * 60)

    # 載入基準地區
    try:
        with open(BASELINE_FILE, encoding='utf-8') as f:
            baseline = json.load(f)
        baseline_found = [loc for loc in baseline if loc['status'] == 'found']
        print(f"載入基準地區：{len(baseline_found)} 個（來自 {BASELINE_FILE}）")
    except FileNotFoundError:
        print(f"找不到基準檔案 {BASELINE_FILE}，請先執行 explore 模式")
        return

    if not COMPANIES_TO_MATCH:
        print("請在 COMPANIES_TO_MATCH 中加入要比對的公司名稱")
        return

    finder = CompanyFinder(CHROME_DEBUG_PORT)
    all_company_results = {}

    try:
        for company_entry in COMPANIES_TO_MATCH:
            # 支援直接填字串（公司名）或完整 dict
            if isinstance(company_entry, str):
                company_config = finder.search_company(company_entry)
                if not company_config:
                    print(f"跳過 {company_entry}（無法取得 Glassdoor ID）")
                    continue
            else:
                company_config = company_entry
            company_name = company_config['name']
            print(f"\n{'='*60}")
            print(f"正在處理：{company_name}")
            results = finder.match_against_baseline(company_config, baseline_found)
            finder.print_match_results(results, company_name)
            finder.save_results(results, company_name,
                                output_file=f"data/{company_name.lower().replace(' ', '_')}_matched.json")
            all_company_results[company_name] = results

        # 產生彙整 config.py 片段
        print(f"\n{'='*60}")
        print("config.py 更新內容：")
        print(f"{'='*60}")
        for company_name, results in all_company_results.items():
            print(f"\n    # {company_name}")
            for r in results:
                key = f"'{company_name} {r['baseline_location']} reviews'"
                if r['url']:
                    val = f"'{r['url']}'"
                elif r['status'] == 'not_in_company':
                    val = "''  # 無此國家辦公室"
                else:
                    val = "''  # 有辦公室但無地區 Review 頁面"
                print(f"    {key}: {val},")

    except Exception as e:
        print(f"\n錯誤：{e}")
        import traceback; traceback.print_exc()
    finally:
        finder.close()


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'match'
    if mode == 'explore':
        run_explore()
    elif mode == 'match':
        run_match()
    else:
        print(f"未知模式：{mode}，請使用 explore 或 match")
