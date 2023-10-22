import random
from datetime import datetime, timedelta

from fake_useragent import UserAgent

from src.config import HEADERS

user_agent = UserAgent()


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
