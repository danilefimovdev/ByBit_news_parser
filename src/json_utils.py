import json

import aiofiles

from src.config import JSON_FILE_PATH
from src.models import News


async def get_news_from_json() -> dict:

    try:
        async with aiofiles.open(JSON_FILE_PATH, 'r', newline='') as file:
            data = await file.read()
            json_data = json.loads(data)
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {}
    return json_data


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