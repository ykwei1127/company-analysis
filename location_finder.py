"""
Glassdoor 地區 Review URL 自動探索工具

從 Glassdoor Office Locations 頁面自動抓取各地區的 Review URL，
再整合進 config.py，省去手動搜尋的麻煩。

使用方式：
    python location_finder.py

前置條件：
    已執行 啟動Chrome.bat 並在 Chrome 中登入 Glassdoor
"""

import time
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# ============================================================
# 設定：要探索哪家公司的地區
# ============================================================
COMPANY_CONFIG = {
    'name': 'ASUS',
    'company_id': 'E40093',
    'locations_url': 'https://www.glassdoor.com/Location/All-ASUS-Office-Locations-E40093.htm',
}

CHROME_DEBUG_PORT = 9222
# ============================================================


class LocationFinder:
    def __init__(self, chrome_debugger_port=9222):
        chrome_options = Options()
        chrome_options.add_experimental_option(
            "debuggerAddress", f"127.0.0.1:{chrome_debugger_port}"
        )
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        print(f"已連接到 Chrome (port {chrome_debugger_port})")

    def get_location_review_urls(self, company_config):
        """
        從 Glassdoor Office Locations 頁面抓取各地區的 Review URL。

        策略：
        1. 載入主 Locations 頁面，收集所有城市的 /Location/All-{Company}-{City}-Office-Locations 連結
        2. 逐一進入各城市 Location 頁面，找該城市的 Reviews 連結
        3. 若找不到 review 連結則標示為 None

        Returns:
            list of dict
        """
        url = company_config['locations_url']
        numeric_id = re.sub(r'[^\d]', '', company_config['company_id'])
        company_name = company_config['name']

        print(f"\n正在載入 Office Locations 頁面：{url}")
        self.driver.get(url)
        time.sleep(5)
        self._scroll_to_bottom()
        print("頁面載入完成，開始收集城市連結...")

        # Step 1：收集所有城市的 Location 頁面連結
        city_links = self._collect_city_links(numeric_id)
        print(f"找到 {len(city_links)} 個城市辦公室")

        results = []
        for i, (city_name, city_info) in enumerate(city_links.items(), 1):
            city_loc_url = city_info['url']
            list_rating = city_info['list_rating']
            address = city_info['address']
            print(f"\n[{i}/{len(city_links)}] {city_name} (列表評分: {list_rating})")
            review_url, review_count, page_heading = self._find_review_url_from_city_page(city_loc_url, numeric_id)
            # 從 heading 解析國家，例如 "ASUS Sydney (Australia)" → "Australia"
            country = None
            if page_heading:
                m = re.search(r'\(([^)]+)\)', page_heading)
                country = m.group(1).strip() if m else None
            # fallback：從地址最後一段取國家（"..., United States" → "United States"）
            if not country and address:
                parts = [p.strip() for p in address.split(',')]
                if len(parts) >= 2:
                    country = parts[-1].strip()
            if review_url:
                print(f"  ✅ {page_heading}  國家: {country}  Review URL: {review_url}")
                results.append({
                    'location': city_name,
                    'country': country,
                    'page_heading': page_heading,
                    'list_rating': list_rating,
                    'address': address,
                    'url': review_url,
                    'reviews_count': review_count,
                    'status': 'found',
                })
            else:
                print(f"  ⚠️  無 Review URL  heading: {page_heading}  國家: {country}")
                results.append({
                    'location': city_name,
                    'country': country,
                    'page_heading': page_heading,
                    'list_rating': list_rating,
                    'address': address,
                    'url': None,
                    'reviews_count': None,
                    'status': 'no_review_url',
                })
            time.sleep(2)

        return results

    def _scroll_to_bottom(self):
        """滾動到頁面底部以觸發 lazy load"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _collect_city_links(self, numeric_id):
        """
        從主 Locations 頁面收集各城市的 Location 頁面連結。
        連結格式：/Location/All-{Company}-{City}-Office-Locations-EI_IE{id}...htm
        同時抓取城市的星等評分和地址（來自連結文字）。
        """
        city_links = {}  # city_name -> {'url': ..., 'list_rating': ..., 'address': ...}
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
                # 排除主頁本身（直接是 All-{Company}-Office-Locations，沒有城市名）
                if re.search(rf'All-[^/]+-Office-Locations-E', href) and \
                   not re.search(rf'All-[^/]+-[^/]+-Office-Locations-E', href):
                    continue
                clean_href = href.split('?')[0]
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                city_name = lines[0] if lines else ''
                # 星等：連結文字中的數字（如 3.9）
                rating_match = re.search(r'(\d\.\d)', text)
                list_rating = float(rating_match.group(1)) if rating_match else None
                # 地址：通常是最後一行
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
        """
        進入城市 Location 頁面，找該城市的 Reviews 連結。
        同時抓取城市頁面的 heading（例如 'ASUS Sydney (Australia)'）以取得國家名。
        Review 連結格式：/Reviews/{Company}-{City}-Reviews-EI_IE{id}..._IC/IN/IM{location_id}.htm
        Returns: (review_url, review_count, page_heading)
        """
        self.driver.get(city_loc_url)
        time.sleep(3)

        # 抓城市頁面的 heading，例如 "ASUS Sydney (Australia)"
        page_heading = None
        heading_selectors = ['h1', 'h2', '[class*="heading"]', '[class*="Heading"]', '[class*="title"]']
        for sel in heading_selectors:
            try:
                elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for elem in elems:
                    t = elem.text.strip()
                    # heading 通常包含公司名和城市，可能有括號國家
                    if t and len(t) > 3 and len(t) < 80:
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
                # 要有地區 filter 參數才是特定地區的 review
                if not any(p in href for p in ['_IL.', '_IC', '_IN', '_IM']):
                    continue
                clean_href = href.split('?')[0]
                # 嘗試抓評論數
                count_match = re.search(r'(\d[\d,]*)\s*review', text, re.IGNORECASE)
                count = int(count_match.group(1).replace(',', '')) if count_match else None
                return clean_href, count, page_heading
            except Exception:
                continue
        return None, None, page_heading

    def _extract_location_names(self):
        return []

    def _guess_location_label(self, url, link_text):
        """從 URL 或連結文字猜測地點標籤"""
        # 優先從連結文字取
        if link_text:
            # 例如 "ASUS Reviews in Singapore (52)" → "Singapore"
            m = re.search(r'Reviews?\s+in\s+(.+?)(?:\s*\(|$)', link_text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
            # 例如 "Singapore Reviews" → "Singapore"
            m = re.search(r'^(.+?)\s+Reviews?', link_text, re.IGNORECASE)
            if m and len(m.group(1)) < 50:
                return m.group(1).strip()

        # 從 URL 路徑取
        # 例如 /Reviews/ASUS-Singapore-Reviews-EI_... → Singapore
        m = re.search(r'/Reviews/[^/]+-([A-Z][^-]+)-Reviews-', url)
        if m:
            return m.group(1).strip()

        return url

    def print_results(self, results, company_name):
        """印出結果摘要"""
        found = [r for r in results if r['status'] == 'found']
        not_found = [r for r in results if r['status'] == 'no_review_url']

        print(f"\n{'='*60}")
        print(f"{company_name} 地區 Review URL 探索結果")
        print(f"{'='*60}")
        print(f"✅ 找到 Review URL：{len(found)} 個")
        for r in sorted(found, key=lambda x: x['location']):
            count_str = f"({r['reviews_count']} reviews)" if r['reviews_count'] else ""
            print(f"  {r['location']:<30} {count_str}")
            print(f"    → {r['url']}")

        if not_found:
            print(f"\n⚠️  有辦公室但無 Review URL：{len(not_found)} 個")
            for r in not_found:
                print(f"  {r['location']}")

    def generate_config_snippet(self, results, company_name):
        """產生可貼進 config.py 的 Python dict 片段"""
        lines = [f"    # {company_name}"]
        for r in sorted(results, key=lambda x: (x['status'] != 'found', x['location'])):
            key = f"'{company_name} {r['location']} reviews'"
            if r['url']:
                val = f"'{r['url']}'"
            else:
                val = "''  # 有辦公室但 Glassdoor 無此地區評論頁面"
            lines.append(f"    {key}: {val},")
        return '\n'.join(lines)

    def save_results(self, results, company_name, output_file=None):
        """儲存結果到 JSON 檔，方便後續處理"""
        if output_file is None:
            safe_name = company_name.lower().replace(' ', '_')
            output_file = f"{safe_name}_locations.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n結果已儲存至：{output_file}")

    def close(self):
        pass  # 手動模式不關閉 Chrome


def main():
    print("=" * 60)
    print("Glassdoor 地區 Review URL 自動探索工具")
    print("=" * 60)
    print("\n請確認：")
    print("1. 已執行 啟動Chrome.bat")
    print("2. 已在 Chrome 中登入 Glassdoor")
    finder = LocationFinder(chrome_debugger_port=CHROME_DEBUG_PORT)

    try:
        results = finder.get_location_review_urls(COMPANY_CONFIG)
        company_name = COMPANY_CONFIG['name']

        finder.print_results(results, company_name)

        snippet = finder.generate_config_snippet(results, company_name)
        print(f"\n{'='*60}")
        print("可貼進 config.py 的內容：")
        print(f"{'='*60}")
        print(snippet)

        finder.save_results(results, company_name)

    except Exception as e:
        print(f"\n發生錯誤：{e}")
        import traceback
        traceback.print_exc()
    finally:
        finder.close()


if __name__ == '__main__':
    main()
