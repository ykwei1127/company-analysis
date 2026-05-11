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

class GlassdoorScraper:
    def __init__(self, mode='manual', headless=False, chrome_debugger_port=9222):
        """
        初始化 Glassdoor 爬蟲
        
        Args:
            mode: 'manual' 或 'auto'
                - 'manual': 連接到已登入的 Chrome（推薦，避免反爬蟲）
                - 'auto': 自動啟動新的 Chrome（可能遇到人機驗證）
            headless: 僅在 auto 模式下有效，是否隱藏瀏覽器
            chrome_debugger_port: 僅在 manual 模式下有效，Chrome 調試端口
        """
        self.mode = mode
        chrome_options = Options()
        
        if mode == 'manual':
            # 手動模式：連接到現有 Chrome
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{chrome_debugger_port}")
            print(f"📌 使用手動模式：連接到端口 {chrome_debugger_port} 的 Chrome")
        else:
            # 自動模式：啟動新的 Chrome
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            print(f"📌 使用自動模式：啟動新的 Chrome（headless={headless}）")
        
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
        print(f"正在抓取: {company_name}")
        print(f"URL: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)
            
            # 滾動頁面以觸發動態載入
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            
            data = {
                'Company': company_name,
                'Baseline Location': None,
                'Actual City': None,
                'Overall': None,
                'Recommend': None,
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
                overall_rating = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'p[data-size-variant="lg"]'))
                ).text
                data['Overall'] = float(overall_rating)
                print(f"  ✓ Overall: {overall_rating}")
            except Exception as e:
                print(f"  ⚠ 無法找到整體評分")
            
            # 提取推薦比例
            try:
                recommend_elem = self.driver.find_element(By.CSS_SELECTOR, 'p[data-test="recommendToFriend"]')
                recommend_text = recommend_elem.text
                match = re.search(r'(\d+)%', recommend_text)
                if match:
                    data['Recommend'] = f"{match.group(1)}%"
                    print(f"  ✓ Recommend: {data['Recommend']}")
            except Exception as e:
                print(f"  ⚠ 無法找到推薦比例")
            
            # 提取評論總數
            try:
                review_count_elem = self.driver.find_element(By.CSS_SELECTOR, '.ReviewOverview_count__xexV9')
                review_text = review_count_elem.get_attribute('textContent')
                match = re.search(r'([\d,]+)', review_text)
                if match:
                    data['Total Reviews'] = match.group(1)
                    print(f"  ✓ Total Reviews: {data['Total Reviews']}")
            except Exception as e:
                print(f"  ⚠ 無法找到評論總數")
            
            # 提取各項評分
            try:
                rating_items = self.driver.find_elements(By.CSS_SELECTOR, '.RatingsByCategory_ratingItem__4EMZd')
                
                for item in rating_items:
                    try:
                        rating_value = item.find_element(By.CSS_SELECTOR, '.RatingsByCategory_rating__T0v8N').text
                        category_label = item.find_element(By.CSS_SELECTOR, '.RatingsByCategory_ratingLabel__o3Me9').text
                        
                        if 'Diversity' in category_label or 'inclusion' in category_label:
                            data['Diversity & Inclusion'] = float(rating_value)
                            print(f"  ✓ Diversity & Inclusion: {rating_value}")
                        elif 'Work/Life' in category_label or 'Work-Life' in category_label:
                            data['Work/Life Balance'] = float(rating_value)
                            print(f"  ✓ Work/Life Balance: {rating_value}")
                        elif 'Compensation' in category_label or 'benefits' in category_label:
                            data['Compensation and Benefits'] = float(rating_value)
                            print(f"  ✓ Compensation and Benefits: {rating_value}")
                        elif 'Culture' in category_label or 'values' in category_label:
                            data['Culture & Values'] = float(rating_value)
                            print(f"  ✓ Culture & Values: {rating_value}")
                        elif 'Career' in category_label or 'opportunities' in category_label:
                            data['Career Opportunities'] = float(rating_value)
                            print(f"  ✓ Career Opportunities: {rating_value}")
                        elif 'Senior' in category_label or 'management' in category_label:
                            data['Senior Management'] = float(rating_value)
                            print(f"  ✓ Senior Management: {rating_value}")
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"  ⚠ 提取評分時發生錯誤: {str(e)}")
            
            # 檢查缺失的數據
            missing_fields = [key for key, value in data.items() if key != 'Company' and value is None]
            if missing_fields:
                print(f"  ⚠ 缺失欄位: {', '.join(missing_fields)}")
            
            print(f"✓ 成功抓取 {company_name}")
            return data
            
        except Exception as e:
            print(f"✗ 抓取 {company_name} 時發生錯誤: {str(e)}")
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
            print()
        
        return all_data

    def scrape_from_matched_json(self, json_files):
        """
        從 company_finder.py 產生的 *_matched.json 抓取評分數據。
        保留 baseline_location 和 matched_city，讓 Excel 顯示正確。

        Args:
            json_files: list of str，matched json 路徑

        Returns:
            list of dict
        """
        import json
        all_data = []

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

                display_name = f"{company} - {baseline_loc}"
                data = self.extract_rating_data(url, display_name)
                if data:
                    data['Baseline Location'] = baseline_loc
                    data['Actual City'] = actual_city
                    all_data.append(data)
                time.sleep(3)
                print()

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
        base_cols = ['Company', 'Baseline Location', 'Actual City', 'Overall', 'Recommend',
                     'Total Reviews', 'Diversity & Inclusion', 'Work/Life Balance',
                     'Compensation and Benefits', 'Culture & Values',
                     'Career Opportunities', 'Senior Management']
        columns_order = [c for c in base_cols if c in df.columns]
        df = df[columns_order]
        
        # 保存為 Excel
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"\n✓ 數據已保存至: {output_file}")
        
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
    
    def close(self):
        """關閉瀏覽器"""
        if self.mode == 'auto':
            self.driver.quit()
        else:
            # 手動模式不關閉瀏覽器
            pass


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

    # 載入配置
    config = load_config()
    scraper_config = getattr(config, 'SCRAPER_CONFIG', {}) if config else {}
    output_config = getattr(config, 'OUTPUT_CONFIG', {}) if config else {}
    mode = scraper_config.get('mode', 'manual')
    headless = scraper_config.get('headless', False)
    output_file = output_config.get('filename', 'data/glassdoor_ratings.xlsx')

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

    try:
        scraper = GlassdoorScraper(mode=mode, headless=headless)

        if matched_files:
            print(f"\n找到 matched JSON：{matched_files}")
            print(f"開始從 matched JSON 抓取數據...\n")
            data = scraper.scrape_from_matched_json(matched_files)
        elif config and hasattr(config, 'COMPANY_URLS'):
            companies = config.COMPANY_URLS
            print(f"\n開始抓取 {len(companies)} 個公司的數據...\n")
            data = scraper.scrape_multiple_companies(companies)
        else:
            print("找不到 matched JSON 也沒有 config.py，請先執行 company_finder.py match")
            return

        if data:
            scraper.save_to_excel(data, output_file)
            print(f"\n✓ 完成！共抓取 {len(data)} 筆數據")
        else:
            print("\n✗ 沒有成功抓取任何數據")

    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        if mode == 'manual':
            print("\n請確認 Chrome 是否已用 --remote-debugging-port=9222 啟動")
    finally:
        scraper.close()


if __name__ == '__main__':
    main()
