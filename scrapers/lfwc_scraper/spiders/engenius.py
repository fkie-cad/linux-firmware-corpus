import json
from datetime import datetime
from json import JSONDecodeError
from typing import Generator

from scrapy import Request
from scrapy.http import Response
from typing_extensions import override

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class Engenius(FirmwareSpider):
    name = "engenius"
    manufacturer = "engenius"

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
            url=f"https://www.engeniusnetworks.eu/wp-json/wp/v2/file?status=publish&page=1&per_page=100&type=file",
            callback=self.parse_page,
            cb_kwargs={"current_page": 1},
        )

    def parse_page(self, response: Response, current_page: int, **_) -> Generator[Request | FirmwareItem, None, None]:
        try:
            data = json.loads(response.body.decode())
        except (UnicodeDecodeError, JSONDecodeError):
            return

        for item in data:
            if item["acf"]["type"].lower() != "firmware":
                continue
            download_link = item["acf"]["download_link"]["url"]
            release_date = datetime.strptime(
                item["acf"]["download_link"]["date"].split(" ")[0], "%Y-%m-%d"
            ).isoformat()
            firmware_version = item["acf"]["version"]
            try:
                device_class = item["pure_taxonomies"]["categories"][0]["category_nicename"]
            except Exception:
                device_class = "unknown"
            device_name = item["acf"]["download_link"]["name"]
            meta_data = {
                "vendor": "engenius",
                "release_date": release_date,
                "device_name": device_name,
                "firmware_version": firmware_version,
                "device_class": device_class,
                "file_urls": download_link,
            }
            yield from self.item_pipeline(meta_data)

        yield Request(
            url="https://www.engeniusnetworks.eu/wp-json/wp/v2/file?status=publish"
            f"&page={current_page + 1}&per_page=100&type=file",
            callback=self.parse_page,
            cb_kwargs={"current_page": current_page + 1},
        )
