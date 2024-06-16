import json
from datetime import datetime
from json import JSONDecodeError
from typing import Generator

from scrapy import Request
from scrapy.http import Response
from typing_extensions import override

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class Ubiquiti(FirmwareSpider):
    name = "ubiquiti"
    manufacturer = "ubiquiti"

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    @override
    def start_requests(self):
        yield Request(
            url=f"https://download.svc.ui.com/v1/downloads?page=1",
            callback=self.parse_page,
            cb_kwargs={"current_page": 1},
        )

    def parse_page(self, response: Response, current_page: int, **_) -> Generator[Request | FirmwareItem, None, None]:
        try:
            data = json.loads(response.body.decode())
        except (UnicodeDecodeError, JSONDecodeError):
            return

        for item in data["downloads"]:
            if item["category"]["name"].lower() != "firmware":
                continue
            download_link = item["file_path"]
            release_date = datetime.fromisoformat(item["date_published"]).isoformat()
            firmware_version = item["version"]
            device_name = item["name"]
            device_class = device_name
            meta_data = {
                "vendor": "ubiquiti",
                "release_date": release_date,
                "device_name": device_name,
                "firmware_version": firmware_version,
                "device_class": device_class,
                "file_urls": download_link,
            }
            yield from self.item_pipeline(meta_data)

        next_page = current_page + 1
        if next_page > data["pagination"]["totalPages"]:
            return
        yield Request(
            url=f"https://download.svc.ui.com/v1/downloads?page={next_page}",
            callback=self.parse_page,
            cb_kwargs={
                "current_page": next_page,
            },
        )
