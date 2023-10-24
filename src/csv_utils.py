import csv
import os

import aiofiles

from src.config import CSV_FILE_PATH, required_keys
from src.json_utils import add_to_last_several_news
from src.models import News
from src.utils import get_datetime_from_seconds


async def add_note_to_csv(news: News) -> bool:
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

        await add_to_last_several_news(news=news)

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