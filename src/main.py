import csv
import json
import os
import random
from datetime import datetime, timedelta
from time import sleep

import requests
from fake_useragent import UserAgent


user_agent = UserAgent()
API_URL = "https://api2.bybit.com/announcements/api/search/v1/index/announcement-posts_en-us"
HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76",
    'Origin': 'https://announcements.bybit.com',
    'Accept': 'application/json, text/plain, */*'
}
DOMAIN = "https://announcements.bybit.com/en-US"
required_keys = ['title', 'date_timestamp', 'url']


class News:
    def __init__(self, title: str, date_timestamp: int, url: str):
        self.title = title
        self.date_timestamp = date_timestamp
        self.url = DOMAIN + url

    def to_dict(self):
        return {"title": self.title, "date_timestamp": self.date_timestamp, "url": self.url}


session = requests.Session()
session.headers.update(HEADERS)


def update_news(from_page_number: int = 0):
    """
    Функция проверяет наличие новых новостей и записывает их в csv файл в случае обнаружения.
    :param from_page_number: номер страницы, с которой мы хотим начать проверять и записать новые новости (тем самым
    можем заполнить наш изначально пустой csv файл). По умолчанию будет проверяться первая
    страница.
    """

    prepare_csv_file()
    prepare_json_file()

    if from_page_number > 1:
        for page_number in range(from_page_number, 0, -1):
            check_new_news(page_number=page_number)
    while True:
        check_new_news()


def check_new_news(page_number: int = 0):
    """
    Функция проверяет появились ли новые новости на данной странице с паузой в секунду
    :param page_number: номер страницы, на которой мы будем проверять новости на наличие новых
    """

    items = get_news(page_number=page_number)
    for item in items[::-1]:
        check_is_it_newer_news(news=item)
    sleep(1)


def get_news(page_number: int, hitsPerPage: int = 8) -> list[News]:
    """
    Функция отправляет запрос, получает json и отдает лист с объектами News
    :param page_number: номер страницы, на которой мы будем проверять новости на наличие новых
    :param hitsPerPage: количество новостей на странице
    """

    query_params = {'hitsPerPage': hitsPerPage, 'page': page_number, 'query': ""}
    change_headers()
    print(HEADERS)
    response = requests.post(url=API_URL, data=query_params, headers=HEADERS)
    json_response = json.loads(response.text)
    items = json_response["result"]["hits"]
    cleared_items = []
    for item in items:
        cleared_item = {key: item[key] for key in required_keys}
        cleared_items.append(News(**cleared_item))
    return cleared_items


def get_datetime_from_seconds(secs: int) -> datetime:
    """
    Функция переводит переданное количество секунд в объект datetime
    :param secs: количество секунд, которое прошло от начало эпохи до даты публикации
    """

    _START_DATETIME = datetime(1970, 1, 1)
    date_timestamp = _START_DATETIME + timedelta(seconds=secs)
    return date_timestamp


def rewrite_the_newest_news(news: News) -> None:
    """
    Функция перезаписывает самую новую новость, с которой мы потом будем сверять все новости
    :param news: новость, которую мы запишем как самую новую
    """

    with open("../static/last_news.json", 'w', newline='') as file:
        json.dump(news.to_dict(), file)


def check_is_it_newer_news(news: News):
    """
    Функция сверяет переданную новость с записанной как "самая новая" в last_news.json по timestamp и title и добавляет
    ее в csv, если она новее. А также переписывает самую новую новость на эту для дальнейшей сверки уже с ней.
    :param news: новость, которую мы будем проверять
    """

    with open("../static/last_news.json", 'r', newline='') as file:
        json_data = json.load(file)
        if not json_data:
            add_note_to_te_csv(news)
            rewrite_the_newest_news(news)
        else:
            newest_news = News(**json_data)
            if news.date_timestamp >= newest_news.date_timestamp and news.title != newest_news.title:
                add_note_to_te_csv(news)
                rewrite_the_newest_news(news)


def add_note_to_te_csv(news: News) -> None:
    """
    Функция создает новую запись новости в csv файле.
    :param news: новость, которую будем записывать.
    """

    note = [value for value in news.to_dict().values()]
    timestamp = get_datetime_from_seconds(note.pop(1))
    note.insert(1, str(timestamp))

    with open("../static/csv_data.csv", 'a+', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(note)


def prepare_csv_file():
    """
    Функция проверяет существует ли файл csv с заголовками и в случае отсутствия (файла или заголовков) исправляет это.
    """

    with open("../static/csv_data.csv", 'a+', newline='', encoding='utf-8') as csv_file:
        csv_file.seek(0)
        first_line = csv_file.readline()
        if first_line != 'title,date_timestamp,url\r\n':
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(required_keys)


def prepare_json_file():
    """
    Функция проверяет существует ли файл csv с заголовками и в случае отсутствия (файла или заголовков) исправляет это.
    """

    if not os.path.exists("../static/last_news.json"):
        with open("../static/last_news.json", 'w', newline='') as file:
            json.dump({}, file)


def change_headers():
    """
    Функция изменяет заголовки и добавляет новые во избежание блокировки или кэширования CDN
    """
    option = random.randint(0, 5)
    header_options = [
        {'Time': str(datetime.utcnow())},
        {'Exchange': random.choice(("ByBIT", ))},
        {'Expire': str(datetime.utcnow() + timedelta(days=option, minutes=option+3, seconds=option+1))},
        {'Required-Data': random.choice(("json", "xml", "xlsx", "txt", ))},
        {'Currency': random.choice(("BTC", "ETH", "XRP", "DASH", "SOL", "BNB", "ADA", "LTC", ))},
    ]
    header_items = random.sample(header_options, option)
    print(header_items)
    for item in header_items:
        for header_name, value in item.items():
            HEADERS[header_name] = value

    # также можно было бы передавать proxy и обезопасить запросы еще больше (не стал использовать какой-то сервис, но
    # просто говорю, что осведомлен об этом)


if __name__ == '__main__':
    update_news(4)
