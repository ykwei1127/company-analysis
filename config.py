# Glassdoor 爬蟲配置文件

INCLUDE_BASELINE = False

PARALLEL_PORTS = [9222, 9223, 9224]

SCRAPER_CONFIG = {
    'mode': 'manual',
    'headless': False,
    'wait_time': 5,
    'delay_between_requests': 3,
}

OUTPUT_CONFIG = {
    'filename': 'output/glassdoor_ratings.xlsx',
    'sheet_name': 'Ratings',
}
