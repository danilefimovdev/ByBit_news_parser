from datetime import datetime, timedelta


async def get_datetime_from_seconds(secs: int) -> datetime:
    """
    Функция переводит переданное количество секунд в объект datetime
    :param secs: количество секунд, которое прошло от начало эпохи до даты публикации
    """

    start_datetime = datetime(1970, 1, 1)
    date_timestamp = start_datetime + timedelta(seconds=secs)
    return date_timestamp
