API_URL = "https://api2.bybit.com/announcements/api/search/v1/index/announcement-posts_en-us"
HEADERS = {
    'Origin': 'https://announcements.bybit.com',
    'Accept': 'application/json, text/plain, */*'
}
DOMAIN = "https://announcements.bybit.com/en-US"

CSV_FILE_PATH = "../static/csv_data.csv"
JSON_FILE_PATH = "../static/last_news.json"
PAUSE_VALUE = 1

required_keys = ['title', 'date_timestamp', 'url']