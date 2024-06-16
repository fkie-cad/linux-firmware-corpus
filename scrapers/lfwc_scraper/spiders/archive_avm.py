import re
from json import loads

from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider


class ArchiveAVM(FirmwareSpider):
    name = "archive_avm"
    allowed_domains = ["web.archive.org"]
    start_urls = [
        "https://web.archive.org/cdx/search/cdx?url=download.avm.de&matchType=prefix&limit=10000"
        "&filter=urlkey:.*(image|zip|bin|raw)$&output=json&filter=!urlkey:.*(misc|other|english|englisch).*"
        "&filter=statuscode:200"
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
            if "develper" in original_url:
                continue
            image_url = f"https://web.archive.org/web/{archive_timestamp}if_/{original_url}"
            meta_data = {
                "vendor": "AVM",
                "source": "archive.org",
                "file_urls": [image_url],
                "device_name": image_url.split("/")[-1],
                "device_class": self.map_device_class(image_path=image_url),
                "firmware_version": "manual",
                "release_date": "",
            }

            yield from self.item_pipeline(meta_data)

    @staticmethod
    def map_device_class(image_path: str) -> str:
        # /fritzbox/<PRODUCT_PARENT>/<locale>/fritz.os/<image>
        if any(substr in image_path.lower() for substr in ["repeater", "repeater"]):
            return "repeater"
        if "fritzwlan-usb" in image_path.lower():
            return "wifi-usb"
        if "powerline" in image_path.lower():
            return "powerline"
        if any(substr in image_path.lower() for substr in ["box.", "box_"]):
            return "router"
        return "unknown"
