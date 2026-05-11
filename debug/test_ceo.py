import sys
sys.path.insert(0, '.')
from glassdoor_scraper_unified import GlassdoorScraper

scraper = GlassdoorScraper(mode='manual')
data = scraper.extract_rating_data(
    'https://www.glassdoor.com/Reviews/NVIDIA-Reviews-E7633.htm',
    'NVIDIA - Global'
)
scraper.close()

print('\n=== 結果 ===')
print(f"Overall:      {data.get('Overall')}")
print(f"Recommend:    {data.get('Recommend')}")
print(f"CEO Approval: {data.get('CEO Approval')}")
