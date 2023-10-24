import asyncio
import sys
from datetime import datetime

import aiohttp

from src.csv_utils import prepare_csv_file
from src.json_utils import create_json_several_news_files
from src.news_utils import check_new_news


async def main(from_page_number: int = 0):
    """
    Функция проверяет наличие новых новостей и записывает их в csv файл в случае обнаружения.
    :param from_page_number: номер страницы, с которой мы хотим начать проверять и записать новые новости (тем самым
    можем заполнить наш изначально пустой csv файл). По умолчанию будет проверяться первая
    страница.
    """

    await prepare_csv_file()
    await create_json_several_news_files()

    async with aiohttp.ClientSession() as session:
        if from_page_number > 1:
            for page_number in range(from_page_number-1, 0, -1):
                print('Send request', datetime.utcnow())
                await check_new_news(page_number=page_number, session=session)
        while True:
            print('Send request', datetime.utcnow())
            await check_new_news(session=session)


if __name__ == '__main__':
    page_number = 3
    try:
        asyncio.run(main(from_page_number=page_number))
    except Exception as ex:
        print(ex)
        print("Script stop working")
        sys.exit()
