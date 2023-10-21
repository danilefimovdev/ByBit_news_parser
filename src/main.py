import csv
import json
import os
import random
import sys
from datetime import datetime, timedelta
from time import sleep

import requests
from fake_useragent import UserAgent
from requests import Session

user_agent = UserAgent()
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


class News:
    def __init__(self, title: str, date_timestamp: int, url: str):
        self.title = title
        self.date_timestamp = date_timestamp
        self.url = DOMAIN + url

    def to_dict(self) -> dict:
        return {"title": self.title, "date_timestamp": self.date_timestamp, "url": self.url}


def main(from_page_number: int = 0):
    """
    Функция проверяет наличие новых новостей и записывает их в csv файл в случае обнаружения.
    :param from_page_number: номер страницы, с которой мы хотим начать проверять и записать новые новости (тем самым
    можем заполнить наш изначально пустой csv файл). По умолчанию будет проверяться первая
    страница.
    """

    session = requests.Session()

    prepare_csv_file()

    if from_page_number > 1:
        for page_number in range(from_page_number-1, 0, -1):
            check_new_news(page_number=page_number, session=session)
    while True:
        check_new_news(session=session)


def check_new_news(session: Session, page_number: int = 0):
    """
    Функция проверяет появились ли новые новости на данной странице с паузой в секунду
    :param page_number: номер страницы, на которой мы будем проверять новости на наличие новых
    """

    items = get_news(session=session, page_number=page_number)
    for item in reversed(items):
        check_is_it_newer_news(news=item)  # TODO: выполнить асинхронно
    sleep(PAUSE_VALUE)


def check_is_it_newer_news(news: News):
    """
    Функция сверяет переданную новость с записанной как "самая новая" в last_news.json по timestamp и title и добавляет
    ее в csv, если она новее. А также переписывает самую новую новость на эту для дальнейшей сверки уже с ней.
    :param news: новость, которую мы будем проверять
    """

    try:
        with open(JSON_FILE_PATH, 'r', newline='') as file:
            json_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {}

    newest_news = News(**json_data) if json_data else None
    if not newest_news or (news.date_timestamp >= newest_news.date_timestamp and news.title != newest_news.title):
        add_note_to_te_csv(news)
        rewrite_the_newest_news(news)


def get_news(session: Session, page_number: int, hitsPerPage: int = 8) -> list[News]:
    """
    Функция отправляет запрос, получает json и отдает лист с объектами News
    :param page_number: номер страницы, на которой мы будем проверять новости на наличие новых
    :param hitsPerPage: количество новостей на странице
    """

    query_params = {'hitsPerPage': hitsPerPage, 'page': page_number, 'query': ""}
    headers = create_new_headers()
    print(headers)
    response = session.post(url=API_URL, data=query_params, headers=headers)
    response_data = response.json()
    items = response_data.get('result', {}).get('hits', [])
    news_list = [News(title=item['title'], date_timestamp=item['date_timestamp'], url=item['url']) for item in items]
    return news_list


def get_datetime_from_seconds(secs: int) -> datetime:
    """
    Функция переводит переданное количество секунд в объект datetime
    :param secs: количество секунд, которое прошло от начало эпохи до даты публикации
    """

    start_datetime = datetime(1970, 1, 1)
    date_timestamp = start_datetime + timedelta(seconds=secs)
    return date_timestamp


def rewrite_the_newest_news(news: News) -> bool:
    """
    Функция перезаписывает самую новую новость, с которой мы потом будем сверять все новости
    :param news: новость, которую мы запишем как самую новую
    """

    try:
        with open(JSON_FILE_PATH, 'w', newline='') as file:
            json.dump(news.to_dict(), file)
        return True
    except Exception as e:
        print(f"Ошибка при перезаписи новости: {str(e)}")
        return False


def add_note_to_te_csv(news: News) -> bool:
    """
    Функция создает новую запись новости в csv файле.
    :param news: новость, которую будем записывать.
    """

    try:
        note = [value for value in news.to_dict().values()]
        timestamp = get_datetime_from_seconds(note.pop(1))
        note.insert(1, str(timestamp))

        with open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(note)
        return True
    except Exception as e:
        print(f"Error with csv: {str(e)}")
        return False


def prepare_csv_file() -> None:
    """
    Функция проверяет существует ли файл csv с заголовками и в случае отсутствия (файла или заголовков) исправляет это.
    """

    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(required_keys)
    else:
        with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            first_row = next(reader, None)
            if first_row != required_keys:
                with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(required_keys)


async def generate_time_header() -> dict:
    return {'Time': str(datetime.utcnow())}


async def generate_exchange_header() -> dict:
    return {'Exchange': random.choice(["ByBIT"])}


async def generate_expire_header(option: int) -> dict:

    expiration_time = datetime.utcnow() + timedelta(days=option, minutes=option + 3, seconds=option + 1)
    return {'Expire': str(expiration_time)}


async def generate_required_data_header() -> dict:
    return {'Required-Data': random.choice(["json", "xml", "xlsx", "txt"])}


async def generate_currency_header() -> dict:
    return {'Currency': random.choice(["BTC", "ETH", "XRP", "DASH", "SOL", "BNB", "ADA", "LTC"])}


def create_new_headers() -> dict:
    """
    Функция изменяет заголовки и добавляет новые во избежание блокировки или кэширования CDN
    """

    option = random.randint(0, 5)
    ua = user_agent.random

    header_options = [
        {'Time': generate_time_header},
        {'Exchange': generate_exchange_header},
        {'Expire': generate_expire_header},
        {'Required-Data': generate_required_data_header},
        {'Currency': generate_currency_header},
    ]

    selected_headers = random.sample(header_options, option)
    new_headers = dict()
    new_headers.update(HEADERS)
    new_headers["User-Agent"] = ua

    coroutines = []

    for item in selected_headers:
        for header_name, function_ in item.items():
            if header_name == 'Expire':
                new_headers.update(function_(option))
            else:
                new_headers.update(function_())

    return new_headers
    # также можно было бы передавать proxy и обезопасить запросы еще больше (не стал использовать какой-то сервис, но
    # просто говорю, что осведомлен об этом)


if __name__ == '__main__':
    page_number = 4
    try:
        main(from_page_number=page_number)
    except KeyboardInterrupt:
        print("Script stop working")
        sys.exit()



#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------


# async def update_news(session, from_page_number=1):
#     await prepare_csv_file()
#     await prepare_json_file()
#
#     if from_page_number > 1:
#         for page_number in range(from_page_number, 0, -1):
#             await check_new_news(page_number, session)
#     while True:
#         await check_new_news(1, session)
#
#
# async def check_new_news(page_number, session):
#     items = await get_news(page_number, session)
#     coroutines = [process_news_item(item) for item in items[::-1]]
#     await asyncio.gather(*coroutines)
#     await asyncio.sleep(PAUSE_VALUE)
#
#
# async def process_news_item(item):
#     try:
#         await check_is_it_newer_news(item)
#     except Exception as ex:
#         print(f'Error with next news: {item}, {ex}')
#
#
# async def check_is_it_newer_news(news):
#     try:
#         with open(JSON_FILE_PATH, 'r', newline='') as file:
#             json_data = json.load(file)
#     except (FileNotFoundError, json.JSONDecodeError) as ex:
#         print("Error: ",  ex)
#
#     newest_news = News(**json_data) if json_data else None
#     if not newest_news or (news.date_timestamp >= newest_news.date_timestamp and news.title != newest_news.title):
#         await asyncio.gather(
#             add_note_to_csv(news),
#             rewrite_the_newest_news(news)
#         )
#
#
# async def prepare_csv_file():
#     if not os.path.exists(CSV_FILE_PATH):
#         async with aiofiles.open(CSV_FILE_PATH, mode='a', newline='', encoding='utf-8') as file:
#             csv_writer = csv.writer(await file)
#             await csv_writer.writerow(required_keys)
#     else:
#         async with aiofiles.open(CSV_FILE_PATH, mode='r', newline='', encoding='utf-8') as file:
#             first_line = await file.readline()
#             if first_line.strip() != 'title,date_timestamp,url':
#                 async with aiofiles.open(CSV_FILE_PATH, mode='w', newline='', encoding='utf-8') as file:
#                     csv_writer = csv.writer(await file)
#                     await csv_writer.writerow(required_keys)
#
# async def add_note_to_csv(news):
#     note = [value for value in news.to_dict().values()]
#     timestamp = await get_datetime_from_seconds(note.pop(1))
#     note.insert(1, str(timestamp))
#
#     async with aiofiles.open(CSV_FILE_PATH, mode='a', newline='', encoding='utf-8') as file:
#         csv_writer = csv.writer(await file)
#         await csv_writer.writerow(note)
#
#
# async def prepare_json_file():
#     if not os.path.exists(JSON_FILE_PATH):
#         with open(JSON_FILE_PATH, 'w', newline='') as file:
#             json.dump({}, file)
#
#
# async def rewrite_the_newest_news(news):
#     with open(JSON_FILE_PATH, 'w', newline='') as file:
#         json.dump(news.to_dict(), file)
#
#
# def _write_json(data):
#     with open(JSON_FILE_PATH, 'w', newline='') as file:
#         json.dump(data, file)
#
#
# user_agent = UserAgent()
# session = requests.Session()
#
#
# request_lock = asyncio.Lock()
#
#
# async def change_headers(session_: ClientSession):
#     """
#     Функция изменяет заголовки и добавляет рандомно новые во избежание блокировки или кэширования CDN
#     """
#
#     option = random.randint(0, 5)
#
#     # это список всех случайных заголовков
#     header_options_coroutines = [
#         generate_time_header(),
#         generate_exchange_header(),
#         generate_expire_header(option=option),
#         generate_required_data_header(),
#         generate_currency_header()
#     ]
#
#     chosen_header_items = random.sample(header_options_coroutines, option)  # выбираем случайным образом заголовки
#     header_items = await asyncio.gather(*chosen_header_items)
#
#     ua = await asyncio.to_thread(user_agent.random)
#     headers = {"User-Agent": ua}
#
#     headers.update(header_items)
#     async with request_lock:
#         session_.headers.update(headers)
#
#     # также можно было бы передавать proxy и обезопасить запросы еще больше (не стал использовать какой-то сервис, но
#     # просто говорю, что осведомлен об этом)
#
#
# async def fetch_news(session_: ClientSession, page_number, hits_per_page=8):
#     """Функция Отправляет запрос и возвращает список новостей"""
#
#     query_params = {'hitsPerPage': hits_per_page, 'page': page_number, 'query': ""}
#     async with request_lock:
#         await change_headers(session_=session_)
#     print(session_.headers)
#     response = await session_.post(API_URL, data=query_params, headers=HEADERS)
#     response_json = await response.json()
#     return response_json.get("result", {}).get("hits", [])
#
#
# def parse_news(news_data) -> list[News]:
#     """Функция преобразует данные новостей в объекты News"""
#
#     news_list = []
#     for item in news_data:
#         cleared_item = {key: item.get(key) for key in required_keys}
#         news_list.append(News(**cleared_item))
#     return news_list
#
#
# async def get_news(session_: ClientSession, page_number, hits_per_page=8):
#     """Асинхронно получает новости с задержкой между запросами."""
#     news_data = await fetch_news(session_, page_number, hits_per_page)
#     news_list = parse_news(news_data)
#
#     await asyncio.sleep(1)
#
#     return news_list
#
#
# async def get_datetime_from_seconds(secs):
#     _START_DATETIME = datetime(1970, 1, 1)
#     date_timestamp = _START_DATETIME + timedelta(seconds=secs)
#     return date_timestamp
#
#
# async def generate_time_header():
#     """Генерирует заголовок Time с текущим временем UTC"""
#     return {'Time': str(datetime.utcnow())}
#
#
# async def generate_exchange_header():
#     """Генерирует заголовок Exchange с случайным значением"""
#     return {'Exchange': random.choice(["ByBIT"])}
#
#
# async def generate_expire_header(option: int):
#     """Генерирует заголовок Expire с случайным временем"""
#
#     expiration_time = datetime.utcnow() + timedelta(days=option, minutes=option + 3, seconds=option + 1)
#     return {'Expire': str(expiration_time)}
#
#
# async def generate_required_data_header():
#     """Генерирует заголовок Required-Data с случайным значением."""
#     return {'Required-Data': random.choice(["json", "xml", "xlsx", "txt"])}
#
#
# async def generate_currency_header():
#     """Генерирует заголовок Currency с случайным значением."""
#     return {'Currency': random.choice(["BTC", "ETH", "XRP", "DASH", "SOL", "BNB", "ADA", "LTC"])}
#
#
# async def main(page_number_to_start: int = 1):
#     async with aiohttp.ClientSession() as session:
#         await update_news(from_page_number=page_number_to_start)
#
#
# if __name__ == '__main__':
#     page_number = 4
#     asyncio.run(update_news(session=session))