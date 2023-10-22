from src.config import DOMAIN


class News:
    def __init__(self, title: str, date_timestamp: int, url: str):
        self.title = title
        self.date_timestamp = date_timestamp
        self.url = DOMAIN + url

    def to_dict(self) -> dict:
        return {"title": self.title, "date_timestamp": self.date_timestamp, "url": self.url}