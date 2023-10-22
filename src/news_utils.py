import asyncio

from aiohttp import ClientSession

from src.config import API_URL, PAUSE_VALUE
from src.csv_utils import add_note_to_te_csv
from src.headers_utils import create_new_headers
from src.json_utils import rewrite_the_newest_news, get_news_from_json
from src.models import News


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

    json_data = await get_news_from_json()
    newest_news = News(**json_data) if json_data else None
    if not newest_news or (news.date_timestamp >= newest_news.date_timestamp and news.title != newest_news.title):
        print("New news: ", news.to_dict())
        await add_note_to_te_csv(news)
        await rewrite_the_newest_news(news)