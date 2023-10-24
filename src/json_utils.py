import json
import os

import aiofiles

from src.config import JSON_LAST_NEWS_FILE_PATH, KEEP_LAST_NEWS_NUMBER, JSON_LAST_SEVERAL_NEWS_FILE_PATH
from src.models import News


async def get_last_news_from_json() -> dict:
    """
    Функция отдает самую свежую новость
    """
    try:
        async with aiofiles.open(JSON_LAST_NEWS_FILE_PATH, 'r', newline='') as file:
            data = await file.read()
            json_data = json.loads(data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        json_data = {}
    return json_data


async def rewrite_the_newest_news(news: News) -> bool:
    """
    Функция перезаписывает самую новую новость, с которой мы потом будем сверять все новости
    :param news: новость, которую мы запишем как самую новую
    """
    try:
        async with aiofiles.open(JSON_LAST_NEWS_FILE_PATH, 'w', newline='') as file:
            await file.write(json.dumps(news.to_dict()))
        return True
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка при перезаписи новости: {str(e)}")
        return False


async def add_to_last_several_news(news: News) -> None:
    """
    Функция обновляет json файл с несколькими последними новостями (количество задано в KEEP_LAST_NEWS_NUMBER)
    :param news: новость, которую мы добавим в список
    """
    try:
        async with aiofiles.open(JSON_LAST_SEVERAL_NEWS_FILE_PATH, 'r') as r_file:
            data = await r_file.read()
            json_data = json.loads(data)
            news_list = json_data['last_news']
            if len(news_list) == KEEP_LAST_NEWS_NUMBER:
                # здесь мы удаляем самую старую новость в списке
                news_list.pop(KEEP_LAST_NEWS_NUMBER-1)
            # здесь мы добавляем новую новость в начало списке
            news_list.insert(0, news.url)
            json_data['last_news'] = news_list
            async with aiofiles.open(JSON_LAST_SEVERAL_NEWS_FILE_PATH, 'w') as w_file:
                await w_file.write(json.dumps(json_data))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка при перезаписи новости в last_several_news: {str(e)}")


async def get_last_several_news() -> list[str]:
    """
    Функция отдает список с несколькими последними новостями
    """

    try:
        async with aiofiles.open(JSON_LAST_SEVERAL_NEWS_FILE_PATH, 'r', newline='') as file:
            data = await file.read()
            json_data = json.loads(data)['last_news']
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = []
    return json_data


async def prepare_json_several_news_file() -> None:
    """
    Функция подготавливает файл json_several_news, если он не готов
    """
    if not os.path.exists(JSON_LAST_SEVERAL_NEWS_FILE_PATH):
        await create_json_several_news_files()


async def create_json_several_news_files() -> None:
    """
    Функция проверяет существует ли файл json_several_news и в случае отсутствия создает его с пустым списком новостей.
    """
    try:
        async with aiofiles.open(JSON_LAST_SEVERAL_NEWS_FILE_PATH, 'w', newline='') as file:
            await file.write(json.dumps({'last_news': []}))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка при создании json файла для последних {KEEP_LAST_NEWS_NUMBER} новостей: {str(e)}")
