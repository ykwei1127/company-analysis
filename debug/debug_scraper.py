"""
診斷工具 - 用於檢查頁面結構和找出問題
"""

from glassdoor_scraper import GlassdoorScraper
import time

def debug_page(url, company_name):
    """診斷單一頁面"""
    scraper = GlassdoorScraper(headless=False)
    
    try:
        print(f"\n{'='*60}")
        print(f"診斷頁面: {company_name}")
        print(f"URL: {url}")
        print(f"{'='*60}\n")
        
        scraper.driver.get(url)
        time.sleep(5)
        
        # 滾動頁面
        scraper.driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        
        # 檢查頁面標題
        print(f"頁面標題: {scraper.driver.title}")
        
        # 檢查是否有整體評分元素
        print("\n檢查關鍵元素:")
        
        # 1. Overall rating
        try:
            from selenium.webdriver.common.by import By
            overall = scraper.driver.find_element(By.CSS_SELECTOR, 'p[data-size-variant="lg"]')
            print(f"✓ 找到 Overall 評分: {overall.text}")
        except:
            print("✗ 找不到 Overall 評分")
            # 嘗試找到任何包含數字的大標題
            try:
                page_source = scraper.driver.page_source
                if "reviews" in page_source.lower():
                    print("  頁面包含 'reviews' 文字")
                else:
                    print("  ⚠ 頁面可能未正確載入")
            except:
                pass
        
        # 2. Recommend
        try:
            recommend = scraper.driver.find_element(By.CSS_SELECTOR, 'p[data-test="recommendToFriend"]')
            print(f"✓ 找到 Recommend: {recommend.text}")
        except:
            print("✗ 找不到 Recommend")
        
        # 3. Total Reviews
        try:
            review_count = scraper.driver.find_element(By.CSS_SELECTOR, '.ReviewOverview_count__xexV9')
            print(f"✓ 找到 Total Reviews: {review_count.text}")
        except:
            print("✗ 找不到 Total Reviews")
        
        # 4. Rating items
        try:
            rating_items = scraper.driver.find_elements(By.CSS_SELECTOR, '.RatingsByCategory_ratingItem__4EMZd')
            print(f"✓ 找到 {len(rating_items)} 個評分項目")
        except:
            print("✗ 找不到評分項目")
        
        # 保存頁面截圖
        screenshot_file = f"debug_{company_name.replace(' ', '_')}.png"
        scraper.driver.save_screenshot(screenshot_file)
        print(f"\n✓ 截圖已保存: {screenshot_file}")
        
        # 等待用戶檢查
        input("\n按 Enter 繼續...")
        
    finally:
        scraper.close()


if __name__ == '__main__':
    # 測試有問題的頁面
    test_urls = {
        'ASUS Taipei reviews': 'https://www.glassdoor.com/Reviews/ASUS-Taipei-Reviews-EI_IE40093.0,4_IL.5,11_IC3271041.htm',
        'ASUS Taiwan reviews': 'https://www.glassdoor.com/Reviews/ASUS-Taiw%C3%A1n-Reviews-EI_IE40093.0,4_IL.5,11_IN240.htm',
    }
    
    for name, url in test_urls.items():
        debug_page(url, name)
