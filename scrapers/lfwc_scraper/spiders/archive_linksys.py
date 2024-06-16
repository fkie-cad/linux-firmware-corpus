import re
from datetime import datetime
from json import loads

from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider


class ArchiveLinksys(FirmwareSpider):
    name = "archive_linksys"
    allowed_domains = ["web.archive.org"]
    start_urls = [
        "https://web.archive.org/cdx/search/cdx?url=downloads.linksys.com&matchType=prefix&limit=10000&output=json"
        "&filter=urlkey:.*firmware.*&filter=!urlkey:.*(txt|pdf)$&filter=mimetype:application.*"
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 10,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    meta_regex = {
        "device_name": re.compile(r"^(?:Produkt|Controller)\s*:\s+(.*)$", flags=re.MULTILINE | re.IGNORECASE),
        "firmware_version": re.compile(r"^Version\s*:\s+(.*)$", flags=re.MULTILINE | re.IGNORECASE),
        "release_date": re.compile(r"^(?:Release-Datum|Build)\s*:\s+(.*)$", flags=re.MULTILINE | re.IGNORECASE),
    }

    def parse(self, response: Response, **_):
        images_in_archive = loads(response.text)[1:]

        for _, archive_timestamp, original_url, _, _, _, _ in images_in_archive:
            image_url = f"https://web.archive.org/web/{archive_timestamp}if_/{original_url}"
            meta_data = {
                "vendor": "linksys",
                "source": ["archive.org"],
                "file_urls": [image_url],
                "device_name": image_url.split("/")[-1],
                "device_class": "manual",
                "firmware_version": "manual",
                "release_date": [datetime.strptime(archive_timestamp, "%Y%m%d%H%M%S").isoformat()],
            }

            yield from self.item_pipeline(meta_data)
