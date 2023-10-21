import asyncio
import csv
import json
import os
import random
import sys
from datetime import datetime, timedelta

import aiofiles
import aiohttp
from aiohttp import ClientSession
from fake_useragent import UserAgent


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


async def main(from_page_number: int = 0):
    """
    Функция проверяет наличие новых новостей и записывает их в csv файл в случае обнаружения.
    :param from_page_number: номер страницы, с которой мы хотим начать проверять и записать новые новости (тем самым
    можем заполнить наш изначально пустой csv файл). По умолчанию будет проверяться первая
    страница.
    """

    await prepare_csv_file()

    async with aiohttp.ClientSession() as session:
        if from_page_number > 1:
            for page_number in range(from_page_number-1, 0, -1):
                print('Send request', datetime.utcnow())
                await check_new_news(page_number=page_number, session=session)
        while True:
            print('Send request', datetime.utcnow())
            await check_new_news(session=session)


async def check_new_news(session: ClientSession, page_number: int = 0):
    """
    Функция проверяет появились ли новые новости на данной странице с паузой в секунду
    :param page_number: номер страницы, на которой мы будем проверять новости на наличие новых
    :param session: сессия, используя которую мы отправляем запрос
    """

    items = await get_news(session=session, page_number=page_number)
    for item in reversed(items):
        await check_is_it_newer_news(news=item)
    await asyncio.sleep(PAUSE_VALUE)


async def check_is_it_newer_news(news: News):
    """
    Функция сверяет переданную новость с записанной как "самая новая" в last_news.json по timestamp и title и добавляет
    ее в csv, если она новее. А также переписывает самую новую новость на эту для дальнейшей сверки уже с ней.
    :param news: новость, которую мы будем проверять
    """

    try:
        async with aiofiles.open(JSON_FILE_PATH, 'r', newline='') as file:
            data = await file.read()
            json_data = json.loads(data)
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {}

    newest_news = News(**json_data) if json_data else None
    if not newest_news or (news.date_timestamp >= newest_news.date_timestamp and news.title != newest_news.title):
        print("New news: ", news.to_dict())
        await add_note_to_te_csv(news)
        await rewrite_the_newest_news(news)


async def get_news(session: ClientSession, page_number: int, hitsPerPage: int = 8) -> list[News]:
    """
    Функция отправляет запрос, получает json и отдает лист с объектами News
    :param page_number: номер страницы, на которой мы будем проверять новости на наличие новых
    :param hitsPerPage: количество новостей на странице
    :param session: сессия, используя которую мы отправляем запрос
    """

    query_params = {'hitsPerPage': hitsPerPage, 'page': page_number, 'query': ""}
    headers = await create_new_headers()

    async with session.post(url=API_URL, data=query_params, headers=headers) as response:
        response_data = await response.json()
        items = response_data.get('result', {}).get('hits', [])
        news_list = [News(title=item['title'], date_timestamp=item['date_timestamp'], url=item['url']) for item in items]
        return news_list


async def get_datetime_from_seconds(secs: int) -> datetime:
    """
    Функция переводит переданное количество секунд в объект datetime
    :param secs: количество секунд, которое прошло от начало эпохи до даты публикации
    """

    start_datetime = datetime(1970, 1, 1)
    date_timestamp = start_datetime + timedelta(seconds=secs)
    return date_timestamp


async def rewrite_the_newest_news(news: News) -> bool:
    """
    Функция перезаписывает самую новую новость, с которой мы потом будем сверять все новости
    :param news: новость, которую мы запишем как самую новую
    """

    try:
        async with aiofiles.open(JSON_FILE_PATH, 'w', newline='') as file:
            await file.write(json.dumps(news.to_dict()))
        return True
    except Exception as e:
        print(f"Ошибка при перезаписи новости: {str(e)}")
        return False


async def add_note_to_te_csv(news: News) -> bool:
    """
    Функция создает новую запись новости в csv файле.
    :param news: новость, которую будем записывать.
    """

    try:
        note = [value for value in news.to_dict().values()]
        timestamp = await get_datetime_from_seconds(note.pop(1))
        note.insert(1, str(timestamp))

        async with aiofiles.open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            await csv_writer.writerow(note)
        return True
    except Exception as e:
        print(f"Error with csv: {str(e)}")
        return False


async def prepare_csv_file() -> None:
    """
    Функция проверяет существует ли файл csv с заголовками и в случае отсутствия (файла или заголовков) исправляет это.
    """
    if not os.path.exists(CSV_FILE_PATH) or not await check_csv_headers():
        await create_csv_file_with_headers()


async def check_csv_headers() -> bool:
    """
    Функция проверяет, соответствуют ли заголовки CSV файлу ожидаемым значениям.
    """
    if not os.path.exists(CSV_FILE_PATH):
        return False
    async with aiofiles.open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as csv_file:
        async for row in csv_file:
            first_row = str(row).strip('\r\n')
            break
        titles = ','.join(map(str, required_keys))
        return first_row == titles


async def create_csv_file_with_headers() -> None:
    """
    Функция создает новый CSV файл с ожидаемыми заголовками.
    """
    async with aiofiles.open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        await csv_writer.writerow(required_keys)


def generate_time_header() -> dict:
    return {'Time': str(datetime.utcnow())}


def generate_exchange_header() -> dict:
    return {'Exchange': random.choice(["ByBIT"])}


def generate_expire_header() -> dict:

    option = random.randint(0, 27)
    expiration_time = datetime.utcnow() + timedelta(days=option, minutes=option + 3, seconds=option + 1)
    return {'Expire': str(expiration_time)}


def generate_required_data_header() -> dict:
    return {'Required-Data': random.choice(["json", "xml", "xlsx", "txt"])}


def generate_currency_header() -> dict:
    return {'Currency': random.choice(["BTC", "ETH", "XRP", "DASH", "SOL", "BNB", "ADA", "LTC"])}


async def create_new_headers() -> dict:
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

    for item in selected_headers:
        for header_name, function_ in item.items():
            new_headers.update(function_())

    return new_headers
    # также можно было бы передавать proxy и обезопасить запросы еще больше (не стал использовать какой-то сервис, но
    # просто говорю, что осведомлен об этом)


if __name__ == '__main__':
    page_number = 1
    try:
        asyncio.run(main(from_page_number=page_number))
    except KeyboardInterrupt or RuntimeError:
        print("Script stop working")
        sys.exit()
