API_URL = "https://api2.bybit.com/announcements/api/search/v1/index/announcement-posts_en-us"
HEADERS = {
    'Origin': 'https://announcements.bybit.com',
    'Accept': 'application/json, text/plain, */*'
}
DOMAIN = "https://announcements.bybit.com/en-US"

CSV_FILE_PATH = "../static/csv_data.csv"
JSON_LAST_NEWS_FILE_PATH = "../static/last_news.json"
JSON_LAST_SEVERAL_NEWS_FILE_PATH = "../static/last_several_news.json"
PAUSE_VALUE = 1
KEEP_LAST_NEWS_NUMBER = 5

required_keys = ['title', 'date_timestamp', 'url']