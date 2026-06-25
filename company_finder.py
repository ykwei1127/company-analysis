"""
Glassdoor 跨公司地區比較工具

三種模式：
1. office：從公司的 Office Locations 頁抓取城市級 Review URL
2. country：用國家 IN code 抓取國家級 Review URL
3. scan：掃描全世界國家，找出有 review 的地區

使用方式：
    python company_finder.py office        # 建立辦公室城市 URL 清單
    python company_finder.py country       # 建立國家級 URL 清單
    python company_finder.py scan          # 掃描全世界國家

前置條件：
    已執行 啟動Chrome.bat 並在 Chrome 中登入 Glassdoor
"""

import time
import re
import json
import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options


class TeeLogger:
    """同時輸出到 stdout 和 log 檔"""
    def __init__(self, filepath):
        self._stdout = sys.stdout
        self._file = open(filepath, 'w', encoding='utf-8')
        sys.stdout = self

    def write(self, data):
        self._stdout.write(data)
        self._stdout.flush()  # Flush pipe immediately for real-time streaming
        self._file.write(data)
        self._file.flush()  # Flush immediately for real-time updates

    def flush(self):
        self._stdout.flush()
        self._file.flush()

    def close(self):
        sys.stdout = self._stdout
        self._file.close()


# ============================================================
# 全域設定
# ============================================================
CHROME_DEBUG_PORT = 9222
# 多 port 平行設定：預設使用 [9222]，可透過環境變數 FINDER_PORTS 覆蓋
# 例如：set FINDER_PORTS=9222,9223,9224
CHROME_DEBUG_PORTS = [int(p.strip()) for p in os.environ.get('FINDER_PORTS', str(CHROME_DEBUG_PORT)).split(',') if p.strip()]
BASELINE_FILE = 'data/asus_office.json'  # ASUS 辦公室 URL 清單

# 比對模式：'city'（原始邏輯，用同國家城市 IC code）或 'country'（國家級 IN code）
MATCH_MODE = 'country'

# Glassdoor 國家 IN codes（固定值）
COUNTRY_IN_CODES = {
    # 北美
    'United States': '1',
    'Canada': '3',
    'Mexico': '173',
    # 歐洲
    'United Kingdom': '4',
    'France': '86',
    'Germany': '96',
    'Spain': '219',
    'Italy': '121',
    'Netherlands': '178',
    'Hungary': '113',
    'Poland': '197',
    'Czech Republic': '62',
    'Turkey': '244',
    'Sweden': '223',
    'Switzerland': '226',
    'Austria': '15',
    'Belgium': '21',
    'Denmark': '63',
    'Finland': '85',
    'Ireland': '119',
    'Norway': '186',
    'Portugal': '199',
    'Romania': '200',
    'Greece': '100',
    'Ukraine': '246',
    'Russia': '201',
    # 亞太
    'India': '115',
    'Japan': '126',
    'South Korea': '135',
    'China': '52',
    'Taiwan': '240',
    'Singapore': '215',
    'Malaysia': '170',
    'Thailand': '239',
    'Indonesia': '116',
    'Philippines': '196',
    'Vietnam': '251',
    'Australia': '16',
    'New Zealand': '180',
    'Hong Kong': '109',
    # 中東
    'United Arab Emirates': '247',
    'Israel': '120',
    'Saudi Arabia': '207',
    # 南美
    'Brazil': '36',
    'Chile': '51',
    'Argentina': '11',
    'Colombia': '56',
    'Peru': '195',
    # 非洲
    'South Africa': '216',
    'Nigeria': '183',
    'Egypt': '73',
}

# 首次探索用（explore 模式）
EXPLORE_CONFIG = {
    'name': 'ASUS',
    'company_id': 'E40093',
    'locations_url': 'https://www.glassdoor.com/Location/All-ASUS-Office-Locations-E40093.htm',
}

# 比對模式：只需填入公司名稱，ID 和 URL 會自動從 Glassdoor 搜尋
COMPANIES_TO_MATCH = [
    {
        'name': 'ASUS',
        'company_id': 'E40093',
        'locations_url': 'https://www.glassdoor.com/Location/All-ASUS-Office-Locations-E40093.htm',
        'global_review_url': 'https://www.glassdoor.com/Reviews/ASUS-Reviews-E40093.htm',
        'slug': 'ASUS',
    },
    'NVIDIA',
    'TSMC',
    'MSI',
    {
        'name': 'HP Inc.',
        'company_id': 'E1093161',
        'locations_url': 'https://www.glassdoor.com/Location/All-HP-Inc-Office-Locations-E1093161.htm',
        'global_review_url': 'https://www.glassdoor.com/Reviews/HP-Inc-Reviews-E1093161.htm',
        'slug': 'HP-Inc',
    },
    'Quanta Computer',
    'Wistron',
    'Compal Electronics',
    'Wiwynn',
    'Delta Electronics',
    'Inventec',
    'Pegatron',
    'AU Optronics',
    'Trend Micro Inc.',
    'Dell Technologies',
    'Acer Group',
    'Lenovo',
    'Google',
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
        # Derive slug from config (used for URL construction)
        slug = company_config.get('slug') or (
            url.split('All-')[1].split('-Office-')[0]
            if 'All-' in url else company_name.replace(' ', '-')
        )

        print(f"\n正在載入 Office Locations 頁面：{url}")
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception:
            pass
        self._scroll_to_bottom()
        print("頁面載入完成，開始收集城市連結...")

        city_links = self._collect_city_links(numeric_id)
        print(f"找到 {len(city_links)} 個城市辦公室")

        results = []

        # 1. 首先加入 Global（整體公司評論）
        print("\n[Global] 正在抓取整體公司評論頁面...")
        global_url = company_config.get('global_review_url') or f"https://www.glassdoor.com/Reviews/{slug}-Reviews-E{numeric_id}.htm"
        self.driver.get(global_url)
        time.sleep(2)
        global_review_url = None
        try:
            # 檢測是否有重定向到地區頁面，或停留在主頁面
            current_url = self.driver.current_url
            if f'E{numeric_id}' in current_url and 'Location' not in current_url:
                global_review_url = current_url.split('?')[0]
                print(f"  ✅ Global URL: {global_review_url}")
            else:
                # 嘗試從頁面找主要評論連結
                review_link = self.driver.find_element(By.CSS_SELECTOR, f'a[href*="/Reviews/"][href*="E{numeric_id}"]')
                if review_link:
                    global_review_url = review_link.get_attribute('href').split('?')[0]
                    print(f"  ✅ Global URL (from link): {global_review_url}")
        except Exception:
            pass

        if global_review_url:
            results.append({
                'location': 'Global',
                'country': 'Global',
                'page_heading': company_name,
                'heading_is_generic': False,
                'list_rating': None,
                'address': 'Global',
                'url': global_review_url,
                'reviews_count': None,
                'status': 'found',
            })
        else:
            results.append({
                'location': 'Global',
                'country': 'Global',
                'page_heading': company_name,
                'heading_is_generic': True,
                'list_rating': None,
                'address': 'Global',
                'url': None,
                'reviews_count': None,
                'status': 'no_review_url',
            })

        # 2. 加入 Taiwan（國家級別）- 用 IN240 代碼建立
        print("\n[Taiwan] 加入國家級別台灣評論頁面...")
        company_slug = slug
        slug_len = len(company_slug)
        # URL pattern: {slug}-Taiwan-Reviews-EI_IE{id}.0,{slug_len}_IL.{slug_len+1},{slug_len+7}_IN240.htm
        # e.g. ASUS(4) → .0,4_IL.5,11_IN240
        taiwan_url = (
            f"https://www.glassdoor.com/Reviews/{company_slug}-Taiwan-Reviews-"
            f"EI_IE{numeric_id}.0,{slug_len}_IL.{slug_len+1},{slug_len+7}_IN240.htm"
        )
        # 驗證 URL 是否存在（直接嘗試訪問）
        self.driver.get(taiwan_url)
        time.sleep(2)
        taiwan_exists = str(numeric_id) in self.driver.current_url and 'Taiwan' in self.driver.current_url

        if taiwan_exists:
            print(f"  ✅ Taiwan URL: {taiwan_url}")
            results.append({
                'location': 'Taiwan',
                'country': 'Taiwan',
                'page_heading': f'{company_name} Taiwan',
                'heading_is_generic': False,
                'list_rating': None,
                'address': 'Taiwan',
                'url': taiwan_url,
                'reviews_count': None,
                'status': 'found',
            })
        else:
            print(f"  ⚠️  Taiwan URL 可能不存在或需要驗證")
            results.append({
                'location': 'Taiwan',
                'country': 'Taiwan',
                'page_heading': f'{company_name} Taiwan',
                'heading_is_generic': True,
                'list_rating': None,
                'address': 'Taiwan',
                'url': taiwan_url,  # 仍然保存 URL 讓使用者可以手動檢測
                'reviews_count': None,
                'status': 'found',  # 假設存在，實際 match 時會驗證
            })

        # 3. 抓取各城市辦公室
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
        slug = company_config.get('slug') or company_config['locations_url'].split('All-')[1].split('-Office-')[0]
        url = company_config['locations_url']

        # 建立基準地區 IC Code mapping（用於 fallback probe）
        ic_map = self._build_ic_map(baseline_locations)

        print(f"\n正在載入 {company_name} Office Locations 頁面：{url}")
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception:
            pass
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
            # Special case: if baseline_location equals the country name (e.g. "Taiwan"),
            # treat it as country-level and use IN code directly instead of finding a city.
            if ref_location == ref_country:
                in_code = COUNTRY_IN_CODES.get(ref_country)
                if in_code:
                    country_label = ref_country.replace(' ', '-')
                    probe_url, probe_count, _ = self._probe_url_by_ic(
                        slug, numeric_id, country_label,
                        {'code': in_code, 'type': 'IN'}
                    )
                    if probe_url:
                        print(f"  ✅ Country-level URL (IN={in_code})：{probe_url}")
                        results.append({
                            'baseline_location': ref_location,
                            'baseline_country': ref_country,
                            'company': company_name,
                            'matched_city': ref_country,
                            'url': probe_url,
                            'reviews_count': probe_count,
                            'status': 'found',
                        })
                    else:
                        print(f"  ➖ {company_name} 在 {ref_country} 無 review 頁面")
                        results.append({
                            'baseline_location': ref_location,
                            'baseline_country': ref_country,
                            'company': company_name,
                            'matched_city': None,
                            'url': None,
                            'reviews_count': None,
                            'status': 'not_in_company',
                        })
                else:
                    print(f"  ⚠️  無 IN code mapping for {ref_country}，跳過")
                    results.append({
                        'baseline_location': ref_location,
                        'baseline_country': ref_country,
                        'company': company_name,
                        'matched_city': None,
                        'url': None,
                        'reviews_count': None,
                        'status': 'no_in_code',
                    })
                continue

            matched_city = None
            matched_info = None
            for country, (city_name, city_info) in country_to_city.items():
                if self._country_match(ref_country, country):
                    matched_city = city_name
                    matched_info = city_info
                    break

            if not matched_city:
                # Locations 頁找不到 → 用 IC/IN Code 直接 probe
                code_info = ic_map.get(ref_location)
                if code_info:
                    city_label = ref_location.split(',')[0].strip()  # e.g. "Taipei" or "Taiwan"
                    probe_url, probe_count, _ = self._probe_url_by_ic(slug, numeric_id, city_label, code_info)
                    if probe_url:
                        print(f"  ✅ IC probe 找到 Review URL：{probe_url}")
                        results.append({
                            'baseline_location': ref_location,
                            'baseline_country': ref_country,
                            'company': company_name,
                            'matched_city': city_label,
                            'url': probe_url,
                            'reviews_count': probe_count,
                            'status': 'found',
                        })
                        continue
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
                # city 頁找不到 review URL → 用 IC/IN Code probe
                code_info = ic_map.get(ref_location)
                if code_info:
                    city_label = ref_location.split(',')[0].strip()
                    probe_url, probe_count, _ = self._probe_url_by_ic(slug, numeric_id, city_label, code_info)
                    if probe_url:
                        print(f"  ✅ IC probe 找到 Review URL：{probe_url}")
                        results.append({
                            'baseline_location': ref_location,
                            'baseline_country': ref_country,
                            'company': company_name,
                            'matched_city': city_label,
                            'url': probe_url,
                            'reviews_count': probe_count,
                            'status': 'found',
                        })
                        time.sleep(1)
                        continue
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
            time.sleep(1)

        return results

    # ----------------------------------------------------------------
    # Country-level 比對模式
    # ----------------------------------------------------------------
    def match_by_country(self, company_config, baseline_locations):
        """
        以國家級 IN code 直接拼 URL 取得每家公司在各國的 review 頁面。
        不需要載入 Office Locations 頁，速度快且比較基準一致。

        Returns:
            list of dict，每筆對應一個基準國家
        """
        numeric_id = re.sub(r'[^\d]', '', company_config['company_id'])
        company_name = company_config['name']
        if company_config.get('slug'):
            slug = company_config['slug']
        elif company_config.get('locations_url'):
            try:
                slug = company_config['locations_url'].split('All-')[1].split('-Office-')[0]
            except (IndexError, AttributeError):
                slug = company_name.replace(' ', '-')
        else:
            slug = company_name.replace(' ', '-')
        global_review_url = company_config.get('global_review_url')

        # 收集需要比對的國家（從 baseline 中有 review 的地區）
        baseline_found = [loc for loc in baseline_locations if loc['status'] == 'found']

        # 去重國家（一個國家只比一次）
        seen_countries = set()
        country_baselines = []
        for loc in baseline_found:
            if loc['location'] == 'Global':
                country_baselines.append(loc)
                continue
            country = loc['country']
            if country and country not in seen_countries:
                seen_countries.add(country)
                country_baselines.append(loc)

        results = []
        print(f"\n國家級比對模式：{company_name}，共 {len(country_baselines)} 筆（Global + {len(seen_countries)} 國）")

        for i, baseline in enumerate(country_baselines, 1):
            ref_location = baseline['location']
            ref_country = baseline.get('country')

            # Global
            if ref_location == 'Global':
                print(f"  [{i}/{len(country_baselines)}] Global")
                if global_review_url:
                    print(f"    ✅ {global_review_url}")
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

            # 國家級 — 用 IN code probe
            in_code = COUNTRY_IN_CODES.get(ref_country)
            print(f"  [{i}/{len(country_baselines)}] {ref_country} (IN={in_code or '?'})")

            if not in_code:
                print(f"    ⚠️  無 IN code mapping，跳過")
                results.append({
                    'baseline_location': ref_location,
                    'baseline_country': ref_country,
                    'company': company_name,
                    'matched_city': None,
                    'url': None,
                    'reviews_count': None,
                    'status': 'no_in_code',
                })
                continue

            # 拼 country-level review URL
            country_label = ref_country.replace(' ', '-')
            probe_url, probe_count, _ = self._probe_url_by_ic(
                slug, numeric_id, country_label,
                {'code': in_code, 'type': 'IN'}
            )

            if probe_url:
                print(f"    ✅ {probe_url}")
                results.append({
                    'baseline_location': ref_location,
                    'baseline_country': ref_country,
                    'company': company_name,
                    'matched_city': ref_country,  # country-level
                    'url': probe_url,
                    'reviews_count': probe_count,
                    'status': 'found',
                })
            else:
                print(f"    ➖ {company_name} 在 {ref_country} 無 review 頁面")
                results.append({
                    'baseline_location': ref_location,
                    'baseline_country': ref_country,
                    'company': company_name,
                    'matched_city': None,
                    'url': None,
                    'reviews_count': None,
                    'status': 'not_in_company',
                })
            time.sleep(3)

        return results

    # ----------------------------------------------------------------
    # Scan All Countries
    # ----------------------------------------------------------------
    def scan_all_countries(self, company_config):
        """
        掃描 COUNTRY_IN_CODES 中所有國家，找出該公司有 review 的國家。
        不需要 baseline，直接 probe 每個國家的 IN code。

        Returns:
            list of dict，每筆一個國家（含 found/not_found status）
        """
        numeric_id = re.sub(r'[^\d]', '', company_config['company_id'])
        company_name = company_config['name']
        if company_config.get('slug'):
            slug = company_config['slug']
        elif company_config.get('locations_url'):
            try:
                slug = company_config['locations_url'].split('All-')[1].split('-Office-')[0]
            except (IndexError, AttributeError):
                slug = company_name.replace(' ', '-')
        else:
            slug = company_name.replace(' ', '-')
        global_review_url = company_config.get('global_review_url')

        results = []
        countries = list(COUNTRY_IN_CODES.items())
        print(f"\n全國家掃描：{company_name}，共 {len(countries)} 國")

        # Global first
        if global_review_url:
            results.append({
                'country': 'Global',
                'in_code': None,
                'company': company_name,
                'url': global_review_url,
                'reviews_count': None,
                'status': 'found',
            })
            print(f"  [0/{len(countries)}] Global ✅")

        adaptive_delay = 3.0  # 基礎延遲，會根據 rate limit 動態調整
        consecutive_success = 0

        for i, (country, in_code) in enumerate(countries, 1):
            country_label = country.replace(' ', '-')

            # 每 5 個國家主動休息，降低被封鎖風險
            if i > 1 and i % 5 == 0:
                rest_time = 8 if adaptive_delay > 3 else 5
                print(f"    💤 批量休息 {rest_time}s...")
                time.sleep(rest_time)

            probe_url, probe_count, was_limited = self._probe_url_by_ic(
                slug, numeric_id, country_label,
                {'code': in_code, 'type': 'IN'}
            )

            # 如果遇到 rate limit，大幅增加後續延遲
            if was_limited:
                adaptive_delay = min(15.0, adaptive_delay + 3.0)
                print(f"    🔒 觸發限流保護，下次延遲調整為 {adaptive_delay:.1f}s")

            if probe_url:
                consecutive_success += 1
                print(f"  [{i}/{len(countries)}] {country} ✅ ({probe_count or '?'} reviews)")
                results.append({
                    'country': country,
                    'in_code': in_code,
                    'company': company_name,
                    'url': probe_url,
                    'reviews_count': probe_count,
                    'status': 'found',
                })
                # 連續成功可稍微降低延遲（最低 2.5 秒）
                if consecutive_success >= 3 and adaptive_delay > 2.5:
                    adaptive_delay = max(2.5, adaptive_delay - 0.3)
            else:
                consecutive_success = 0
                print(f"  [{i}/{len(countries)}] {country} ✗")
                results.append({
                    'country': country,
                    'in_code': in_code,
                    'company': company_name,
                    'url': None,
                    'reviews_count': None,
                    'status': 'not_found',
                })
                # 失敗則增加延遲（rate limit 已在上面額外增加）
                adaptive_delay = min(8.0, adaptive_delay + 0.5)

            time.sleep(adaptive_delay)

        found = sum(1 for r in results if r['status'] == 'found')
        print(f"\n  結果：{found}/{len(results)} 個國家有 review")
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
        try:
            WebDriverWait(self.driver, 8).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception:
            pass

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
                if not href:
                    continue
                if '/Reviews/' not in href:
                    continue
                if numeric_id not in href:
                    continue
                if not any(p in href for p in ['_IL.', '_IC', '_IN', '_IM']):
                    continue
                clean_href = href.split('?')[0]
                text = link.text.strip()
                count_match = re.search(r'(\d[\d,]*)\s*review', text, re.IGNORECASE)
                count = int(count_match.group(1).replace(',', '')) if count_match else None
                return clean_href, count, page_heading
            except Exception:
                continue
        return None, None, page_heading

    def _build_ic_map(self, baseline_locations):
        """從 baseline JSON 的 URL 抽取每個地區的代碼 mapping。
        Returns: dict {baseline_location: {'code': '3271041', 'type': 'IC'}}
        type 可為 'IC'（城市）或 'IN'（國家）
        """
        ic_map = {}
        for loc in baseline_locations:
            url = loc.get('url') or ''
            m = re.search(r'_(IC|IN)(\d+)\.htm', url)
            if m:
                ic_map[loc['location']] = {'code': m.group(2), 'type': m.group(1)}
        return ic_map

    def _is_rate_limited(self):
        """偵測 Glassdoor rate limit 頁面（Help Us Protect Glassdoor）"""
        try:
            title = self.driver.title.strip().lower()
            if 'security' in title:
                return True
            page_source = self.driver.page_source[:2000].lower()
            if 'help us protect glassdoor' in page_source:
                return True
        except Exception:
            pass
        return False

    def _probe_url_by_ic(self, slug, numeric_id, city_label, code_info):
        """用 IC/IN Code 直接拼出 Review URL，載入後確認頁面是否有效。
        code_info: {'code': '3271041', 'type': 'IC'} 或 {'code': '218', 'type': 'IN'}
        Returns: (url, reviews_count, was_rate_limited) or (None, None, False)
        """
        code = code_info['code']
        code_type = code_info['type']  # 'IC' or 'IN'
        slug_len = len(slug)
        city_len = len(city_label)
        il_start = slug_len + 1
        il_end = il_start + city_len
        url = (f"https://www.glassdoor.com/Reviews/{slug}-{city_label}-Reviews"
               f"-EI_IE{numeric_id}.0,{slug_len}"
               f"_IL.{il_start},{il_end}_{code_type}{code}.htm")
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 8).until(
                lambda d: d.current_url != 'about:blank' and d.execute_script('return document.readyState') == 'complete'
            )
        except Exception:
            pass

        # 偵測 rate limit，等待後重試一次
        was_rate_limited = False
        if self._is_rate_limited():
            was_rate_limited = True
            print(f"    ⚠️  Rate limited! 等待 60 秒後重試...")
            time.sleep(60)
            self.driver.get(url)
            try:
                WebDriverWait(self.driver, 8).until(
                    lambda d: d.current_url != 'about:blank' and d.execute_script('return document.readyState') == 'complete'
                )
            except Exception:
                pass
            if self._is_rate_limited():
                print(f"    ❌ 仍被封鎖，跳過")
                return None, None, was_rate_limited

        final_url = self.driver.current_url
        # 如果被 redirect 到其他頁則無效
        if f'_{code_type}{code}' not in final_url:
            return None, None, was_rate_limited
        
        # 驗證頁面內容是否包含正確的公司名稱（避免頁面重定向到錯誤內容）
        page_valid = False
        try:
            page_title = self.driver.title.lower()
            page_source = self.driver.page_source.lower()
            # 檢查頁面標題或內容是否包含公司名稱
            if slug.lower() in page_title or slug.lower() in page_source:
                page_valid = True
            # 特殊處理：如果頁面顯示的是其他公司，則無效
            if 'aruba' in page_title or 'aruba' in page_source:
                print(f"    ❌ 頁面被重定向到 Aruba，跳過")
                return None, None, was_rate_limited
        except Exception:
            pass
        
        if not page_valid:
            print(f"    ❌ 頁面內容驗證失敗，可能重定向到錯誤頁面")
            return None, None, was_rate_limited
        
        # 嘗試抓評論數
        count = None
        try:
            m = re.search(r'(\d[\d,]+)\s*(?:Employee\s+)?Reviews?', page_source[:3000], re.IGNORECASE)
            if m:
                count = int(m.group(1).replace(',', ''))
        except Exception:
            pass
        return final_url.split('?')[0], count, was_rate_limited

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
            output_file = f"data/{safe_name}_office.json"
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
        # 先導到首頁避免前一頁殘留連結干擾搜尋結果
        self.driver.get("https://www.glassdoor.com")
        try:
            WebDriverWait(self.driver, 8).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception:
            pass

        search_url = f"https://www.glassdoor.com/Search/results.htm?keyword={company_name.replace(' ', '+')}"
        print(f"\n搜尋：{search_url}")
        self.driver.get(search_url)
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception:
            pass

        import re as re_module
        name_keywords = [re_module.sub(r'[^\w]', '', w).lower() for w in company_name.split() if len(w) > 1]

        all_links = self.driver.find_elements(By.TAG_NAME, 'a')
        for link in all_links:
            try:
                href = link.get_attribute('href') or ''
                # 支援兩種 ID 格式：-E7633 和 EI_IE7633
                m = re.search(r'[-_]E(?:I_IE)?(\d+)(?:\.htm|$|[,.])', href)
                if not m:
                    continue
                # 確認是公司頁，排除 job/salary 等
                if not any(p in href for p in ['/Overview/', '/Reviews/', '/Location/']):
                    continue
                # 驗證 href 包含公司名稱關鍵字，避免抓到殘留的其他公司
                href_lower = href.lower()
                if not all(kw in href_lower for kw in name_keywords):
                    continue
                numeric_id = m.group(1)
                # 從 href 取公司 slug
                slug_match = re.search(r'/(?:Overview|Reviews|Location)/(?:Working-at-)?([^/]+?)-(?:Overview|Reviews|Office-Locations|EI_IE)', href)
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
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception:
            pass
        all_links = self.driver.find_elements(By.TAG_NAME, 'a')
        for link in all_links:
            try:
                href = link.get_attribute('href') or ''
                m = re.search(r'[-_]E(\d+)(?:\.htm|$|[,.])', href)
                if not m:
                    continue
                if '/Overview/' not in href and '/Reviews/' not in href:
                    continue
                href_lower = href.lower()
                if not all(kw in href_lower for kw in name_keywords):
                    continue
                numeric_id = m.group(1)
                slug_match = re.search(r'/(?:Overview|Reviews)/([^/]+)-(?:Overview|Reviews)-(?:EI_IE|E)\d+', href)
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
def run_office():
    """建立公司辦公室城市 URL 清單（原 explore 模式）"""
    print("=" * 60)
    print("模式：建立辦公室城市 URL 清單（Office Location）")
    print("=" * 60)

    # 決定要處理的公司列表
    companies_to_run = COMPANIES_TO_MATCH

    # 檢查環境變數（從後端傳遞的公司列表）
    env_companies = os.environ.get('FINDER_COMPANIES')
    if env_companies:
        selected_names = [n.strip() for n in env_companies.split(',') if n.strip()]
        print(f"從環境變數讀取公司列表：{selected_names}")
        companies_to_run = []
        for entry in COMPANIES_TO_MATCH:
            name = entry if isinstance(entry, str) else entry.get('name')
            if name in selected_names:
                companies_to_run.append(entry)
        print(f"篩選後要處理的公司：{len(companies_to_run)} 個")

    if not companies_to_run:
        print("請在 COMPANIES_TO_MATCH 中加入要處理的公司名稱")
        return

    import time as _time
    _total_start = _time.time()

    # 多 port 平行模式
    if len(CHROME_DEBUG_PORTS) > 1:
        parallel_find(
            CHROME_DEBUG_PORTS, 'office', companies_to_run,
            log_ts=datetime.now().strftime('%Y%m%d_%H%M%S')
        )
    else:
        finder = CompanyFinder(CHROME_DEBUG_PORT)
        try:
            for company_entry in companies_to_run:
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

                results = finder.explore_all_locations(company_config)
                safe_name = company_name.lower().replace(' ', '_')
                finder.save_results(results, company_name,
                                    output_file=f"data/{safe_name}_office.json")
                print(f"\n完成！{company_name} 共 {len(results)} 個地區")

        except Exception as e:
            print(f"\n錯誤：{e}")
            import traceback; traceback.print_exc()
        finally:
            finder.close()

    _total = _time.time() - _total_start
    print(f"\n{'='*60}")
    print(f"⏱  總耗時：{_total:.0f}s（{_total/60:.1f} 分鐘）")
    print(f"{'='*60}")


def run_country(companies=None):
    """建立國家級 URL 清單（原 match --mode country）"""
    print("=" * 60)
    print("模式：建立國家級 URL 清單（Country）")
    print("=" * 60)

    # 載入 ASUS 辦公室清單作為基準地區
    try:
        with open(BASELINE_FILE, encoding='utf-8') as f:
            baseline = json.load(f)
        baseline_found = [loc for loc in baseline if loc['status'] == 'found']
        print(f"載入基準地區：{len(baseline_found)} 個（來自 {BASELINE_FILE}）")
    except FileNotFoundError:
        print(f"找不到基準檔案 {BASELINE_FILE}，請先執行 office 模式建立 ASUS 辦公室清單")
        return

    # 決定要處理的公司列表
    companies_to_run = companies if companies is not None else COMPANIES_TO_MATCH
    
    # 檢查環境變數（從後端傳遞的公司列表）
    env_companies = os.environ.get('FINDER_COMPANIES')
    if env_companies:
        selected_names = [n.strip() for n in env_companies.split(',') if n.strip()]
        print(f"從環境變數讀取公司列表：{selected_names}")
        # 從 COMPANIES_TO_MATCH 中篩選
        companies_to_run = []
        for entry in COMPANIES_TO_MATCH:
            name = entry if isinstance(entry, str) else entry.get('name')
            if name in selected_names:
                companies_to_run.append(entry)
        print(f"篩選後要處理的公司：{len(companies_to_run)} 個")
    
    if not companies_to_run:
        print("請在 COMPANIES_TO_MATCH 中加入要比對的公司名稱")
        return

    import time as _time
    _total_start = _time.time()

    # 多 port 平行模式
    if len(CHROME_DEBUG_PORTS) > 1:
        all_company_results = parallel_find(
            CHROME_DEBUG_PORTS, 'country', companies_to_run,
            baseline=baseline_found, log_ts=datetime.now().strftime('%Y%m%d_%H%M%S')
        )
    else:
        finder = CompanyFinder(CHROME_DEBUG_PORT)
        all_company_results = {}

        try:
            for company_entry in companies_to_run:
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
                _t0 = _time.time()

                results = finder.match_by_country(company_config, baseline_found)

                _elapsed = _time.time() - _t0
                finder.print_match_results(results, company_name)
                finder.save_results(results, company_name,
                                    output_file=f"data/{company_name.lower().replace(' ', '_')}_country.json")
                print(f"  ⏱  {company_name} 耗時：{_elapsed:.0f}s")
                all_company_results[company_name] = results

        except Exception as e:
            print(f"\n錯誤：{e}")
            import traceback; traceback.print_exc()
        finally:
            finder.close()

    # 彙整摘要
    print(f"\n{'='*60}")
    print("比對摘要：")
    print(f"{'='*60}")
    for company_name, results in all_company_results.items():
        found = sum(1 for r in results if r['status'] == 'found')
        print(f"  {company_name}: {found}/{len(results)} 個地區有 review")

    _total = _time.time() - _total_start
    print(f"\n{'='*60}")
    print(f"⏱  總耗時：{_total:.0f}s（{_total/60:.1f} 分鐘）")
    print(f"{'='*60}")


def run_scan():
    """掃描所有國家，找出 COMPANIES_TO_MATCH 中每家公司有 review 的國家。"""
    print("=" * 60)
    print("模式：全國家掃描（Scan All Countries）")
    print(f"掃描 {len(COUNTRY_IN_CODES)} 個國家")
    print("=" * 60)

    # 決定要處理的公司列表
    companies_to_run = COMPANIES_TO_MATCH
    
    # 檢查環境變數（從後端傳遞的公司列表）
    env_companies = os.environ.get('FINDER_COMPANIES')
    if env_companies:
        selected_names = [n.strip() for n in env_companies.split(',') if n.strip()]
        print(f"從環境變數讀取公司列表：{selected_names}")
        # 從 COMPANIES_TO_MATCH 中篩選
        companies_to_run = []
        for entry in COMPANIES_TO_MATCH:
            name = entry if isinstance(entry, str) else entry.get('name')
            if name in selected_names:
                companies_to_run.append(entry)
        print(f"篩選後要處理的公司：{len(companies_to_run)} 個")
    
    if not companies_to_run:
        print("請在 COMPANIES_TO_MATCH 中加入要掃描的公司名稱")
        return

    import time as _time
    _total_start = _time.time()

    # 多 port 平行模式
    if len(CHROME_DEBUG_PORTS) > 1:
        parallel_find(
            CHROME_DEBUG_PORTS, 'scan', companies_to_run,
            log_ts=datetime.now().strftime('%Y%m%d_%H%M%S')
        )
    else:
        finder = CompanyFinder(CHROME_DEBUG_PORT)
        try:
            for company_entry in companies_to_run:
                if isinstance(company_entry, str):
                    company_config = finder.search_company(company_entry)
                    if not company_config:
                        print(f"跳過 {company_entry}（無法取得 Glassdoor ID）")
                        continue
                else:
                    company_config = company_entry
                company_name = company_config['name']
                print(f"\n{'='*60}")
                print(f"掃描：{company_name}")

                results = finder.scan_all_countries(company_config)
                # 儲存完整掃描結果
                finder.save_results(results, company_name,
                                    output_file=f"data/{company_name.lower().replace(' ', '_')}_scan.json")

        except Exception as e:
            print(f"\n錯誤：{e}")
            import traceback; traceback.print_exc()
        finally:
            finder.close()

    _total = _time.time() - _total_start
    print(f"\n{'='*60}")
    print(f"⏱  總耗時：{_total:.0f}s（{_total/60:.1f} 分鐘）")
    print(f"{'='*60}")


def run_city():
    """以 ASUS Office 清單為基準，比對其他公司同國家城市 URL（City Match 模式）"""
    print("=" * 60)
    print("模式：城市比對 URL 清單（City Match）")
    print("=" * 60)

    # 載入 ASUS 辦公室清單作為基準地區
    try:
        with open(BASELINE_FILE, encoding='utf-8') as f:
            baseline = json.load(f)
        baseline_found = [loc for loc in baseline if loc['status'] == 'found']
        print(f"載入基準地區：{len(baseline_found)} 個（來自 {BASELINE_FILE}）")
    except FileNotFoundError:
        print(f"找不到基準檔案 {BASELINE_FILE}，請先執行 office 模式建立 ASUS 辦公室清單")
        return

    # 決定要處理的公司列表
    companies_to_run = COMPANIES_TO_MATCH

    # 檢查環境變數（從後端傳遞的公司列表）
    env_companies = os.environ.get('FINDER_COMPANIES')
    if env_companies:
        selected_names = [n.strip() for n in env_companies.split(',') if n.strip()]
        print(f"從環境變數讀取公司列表：{selected_names}")
        companies_to_run = []
        for entry in COMPANIES_TO_MATCH:
            name = entry if isinstance(entry, str) else entry.get('name')
            if name in selected_names:
                companies_to_run.append(entry)
        print(f"篩選後要處理的公司：{len(companies_to_run)} 個")

    # City mode 以 ASUS 為基準，排除 ASUS 本身（比對自己沒有意義）
    baseline_name = 'ASUS'
    companies_to_run = [
        e for e in companies_to_run
        if (e if isinstance(e, str) else e.get('name')) != baseline_name
    ]
    if not companies_to_run:
        print("沒有其他公司可比對（city mode 不適用於 ASUS 本身）")
        return

    import time as _time
    _total_start = _time.time()

    # 多 port 平行模式
    if len(CHROME_DEBUG_PORTS) > 1:
        all_company_results = parallel_find(
            CHROME_DEBUG_PORTS, 'city', companies_to_run,
            baseline=baseline_found, log_ts=datetime.now().strftime('%Y%m%d_%H%M%S')
        )
    else:
        finder = CompanyFinder(CHROME_DEBUG_PORT)
        all_company_results = {}

        try:
            for company_entry in companies_to_run:
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
                _t0 = _time.time()

                results = finder.match_against_baseline(company_config, baseline_found)

                _elapsed = _time.time() - _t0
                finder.print_match_results(results, company_name)
                safe_name = company_name.lower().replace(' ', '_')
                finder.save_results(results, company_name,
                                    output_file=f"data/{safe_name}_city.json")
                print(f"  ⏱  {company_name} 耗時：{_elapsed:.0f}s")
                all_company_results[company_name] = results

        except Exception as e:
            print(f"\n錯誤：{e}")
            import traceback; traceback.print_exc()
        finally:
            finder.close()

    # 彙整摘要
    print(f"\n{'='*60}")
    print("比對摘要：")
    print(f"{'='*60}")
    for company_name, results in all_company_results.items():
        found = sum(1 for r in results if r['status'] == 'found')
        print(f"  {company_name}: {found}/{len(results)} 個地區有 review")

    _total = _time.time() - _total_start
    print(f"\n{'='*60}")
    print(f"⏱  總耗時：{_total:.0f}s（{_total/60:.1f} 分鐘）")
    print(f"{'='*60}")


# ============================================================
# Parallel URL-list finding across multiple Chrome ports
# ============================================================

def _finder_worker(port, mode, task_queue, log_path=None):
    """Single Chrome port worker: creates one CompanyFinder and processes tasks."""
    import io
    import threading
    import queue as queue_mod

    buf = io.StringIO()
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
                _log_file.flush()

    finder = CompanyFinder(port)
    results_collected = {}
    try:
        while True:
            try:
                task = task_queue.get_nowait()
            except queue_mod.Empty:
                break

            company_config = task['company_config']
            company_name = company_config['name']
            baseline = task.get('baseline')
            safe_name = company_name.lower().replace(' ', '_')
            output_file = f"data/{safe_name}_{mode}.json"
            task_name = f"{company_name} ({mode})"

            _log(f"\n正在處理：{company_name}")
            _t0 = time.time()
            try:
                if mode == 'office':
                    results = finder.explore_all_locations(company_config)
                elif mode == 'country':
                    results = finder.match_by_country(company_config, baseline)
                elif mode == 'city':
                    results = finder.match_against_baseline(company_config, baseline)
                elif mode == 'scan':
                    results = finder.scan_all_countries(company_config)
                else:
                    raise ValueError(f"Unknown mode: {mode}")

                finder.save_results(results, company_name, output_file=output_file)
                results_collected[company_name] = results
                _elapsed = time.time() - _t0
                _log(f"  完成！{company_name} 共 {len(results)} 個地區（{_elapsed:.0f}s）")
                print(f"[DONE] Port {port} {task_name} {len(results)} entries  log: {log_path}", flush=True)
            except Exception as e:
                _log(f"  錯誤：{e}")
                print(f"[ERROR] Port {port} {task_name}: {e}", flush=True)
                # Put task back for other ports to retry
                task_queue.put(task)
                _log(f"[REQUEUE] Port {port} 任務 {task_name} 已放回佇列")
                break
            finally:
                task_queue.task_done()
    finally:
        finder.close()
        if _log_file:
            _log_file.close()

    return results_collected


def _resolve_company_configs(companies, port):
    """Resolve string company names to full configs using a single Chrome port."""
    finder = CompanyFinder(port)
    configs = []
    try:
        for company_entry in companies:
            if isinstance(company_entry, str):
                company_config = finder.search_company(company_entry)
                if not company_config:
                    print(f"跳過 {company_entry}（無法取得 Glassdoor ID）")
                    continue
            else:
                company_config = company_entry
            configs.append(company_config)
    finally:
        finder.close()
    return configs


def parallel_find(ports, mode, companies, baseline=None, log_ts=None):
    """
    多 port 平行抓取 URL list。

    Args:
        ports: list of int，Chrome debugger ports
        mode: 'country', 'city', or 'scan'
        companies: list of company configs or names
        baseline: list of baseline locations（country/city 模式需要）
        log_ts: str，log 檔案時間戳

    Returns:
        dict {company_name: results}
    """
    import threading
    import queue as queue_mod
    from concurrent.futures import ThreadPoolExecutor

    if not ports:
        raise ValueError("ports must not be empty")

    # Pre-resolve company configs using the first port
    print(f"\n預先解析公司資訊（使用 port {ports[0]}）...")
    company_configs = _resolve_company_configs(companies, ports[0])
    if not company_configs:
        print("沒有可處理的公司")
        return {}
    print(f"共 {len(company_configs)} 間公司待處理")

    # Build shared task queue
    task_queue = queue_mod.Queue()
    for company_config in company_configs:
        task = {'company_config': company_config}
        if baseline is not None:
            task['baseline'] = baseline
        task_queue.put(task)

    ts = log_ts or datetime.now().strftime('%Y%m%d_%H%M%S')
    port_logs = {port: f'logs/company_finder_{ts}_port{port}.txt' for port in ports}

    print(f"\n⚡ 平行模式：使用 {len(ports)} 個 Chrome（ports: {ports}）")

    executor = ThreadPoolExecutor(max_workers=len(ports))
    futures = {
        executor.submit(_finder_worker, port, mode, task_queue, port_logs[port]): port
        for port in ports
    }

    all_results = {}
    try:
        for future in futures:
            port = futures[future]
            try:
                port_results = future.result()
                all_results.update(port_results)
                print(f"[DONE] Port {port} completed {len(port_results)} companies", flush=True)
            except Exception as e:
                print(f"[ERROR] Port {port} error: {e}", flush=True)
    except KeyboardInterrupt:
        print("\n[WARN] Ctrl+C received, stopping workers...", flush=True)
        for f in futures:
            f.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise

    executor.shutdown(wait=True)

    if not task_queue.empty():
        remaining = task_queue.qsize()
        print(f"[WARN] {remaining} tasks remaining in queue but all ports stopped.", flush=True)

    return all_results


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'country'
    os.makedirs('logs', exist_ok=True)
    log_path = f"logs/company_finder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = TeeLogger(log_path)
    print(f"Log: {log_path}")
    try:
        if mode == 'office':
            run_office()
        elif mode == 'country':
            run_country()
        elif mode == 'city':
            run_city()
        elif mode == 'scan':
            run_scan()
        # Legacy aliases
        elif mode == 'explore':
            run_office()
        elif mode == 'match':
            run_country()
        else:
            print(f"未知模式：{mode}，請使用 office、country、city 或 scan")
    finally:
        logger.close()
