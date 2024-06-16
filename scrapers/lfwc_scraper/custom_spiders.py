from abc import ABCMeta
from typing import Generator

from scrapy import Spider
from scrapy.loader import ItemLoader

from lfwc_scraper.custom_requests import FTPFileRequest, FTPListRequest
from lfwc_scraper.items import FirmwareItem


class FirmwareSpider(Spider, metaclass=ABCMeta):

    @staticmethod
    def item_pipeline(meta_data: dict) -> Generator[FirmwareItem, None, None]:
        loader = ItemLoader(item=FirmwareItem(), selector=meta_data["file_urls"])
        for key, value in meta_data.items():
            loader.add_value(key, value)
        yield loader.load_item()


class FTPSpider(FirmwareSpider, metaclass=ABCMeta):

    def start_requests(self):
        for url in self.start_urls:
            yield FTPListRequest(url) if url.endswith("/") else FTPFileRequest(url)
