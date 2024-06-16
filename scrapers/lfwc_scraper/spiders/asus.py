import json
import re
from contextlib import suppress
from datetime import datetime
from json import JSONDecodeError
from typing import Generator, List

from scrapy import Request
from scrapy.http import Response
from typing_extensions import override

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class Asus(FirmwareSpider):
    name = "asus"
    manufacturer = "ASUS"

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
        product_type_ids = [
            ("Business Switches", "switch", 24591),
            ("Gaming Networking", "router", 24506),
            ("Gaming Wireless-Router", "router", 25908),
            ("ROG Raming WLAN-Router", "router", 25740),
            ("4G LTE/3G-Router", "router", 3158),
            ("Kabel-Modems & Router", "router", 21981),
            ("Media-Bridge, Repeater und mehr", "repeater", 2619),
            ("Powerline-Adapter", "powerline", 2850),
            ("Wireless-Router", "router", 2542),
            ("WLAN-Mesh-Systeme", "mesh", 25266),
            ("xDSL-Modem-Router", "router", 3081),
            ("Business Switches", "switches", 24676),
            ("Business WLAN Router", "router", 25017),
        ]

        for _, device_class, type_id in product_type_ids:
            yield Request(
                f"https://www.asus.com/support/api/product.asmx/GetPDLevel?website=de&type=2&typeid={type_id}"
                "&productflag=1",
                callback=self.parse_pdlevel,
                cb_kwargs={"device_class": device_class},
            )

    def parse_pdlevel(self, response: Response, device_class: str, **_) -> Generator[Request, None, None]:
        try:
            data = json.loads(response.body.decode())
            print(data)
        except (UnicodeDecodeError, JSONDecodeError):
            yield from []
            return

        for product in data["Result"]["Product"]:
            pd_hashed_id = product["PDHashedId"]
            device_name = re.sub("<[^<]+?>", "", product["PDName"]).strip()
            yield Request(
                url=f"https://www.asus.com/support/api/product.asmx/GetPDBIOS?website=de&model={device_name}"
                f"&pdhashedid={pd_hashed_id}",
                callback=self.parse_pdbios,
                cb_kwargs={"device_name": device_name, "device_class": device_class},
            )

    def parse_pdbios(
        self, response: Response, device_name: str, device_class: str
    ) -> Generator[FirmwareItem, None, None]:
        try:
            data = json.loads(response.body.decode())
        except (UnicodeDecodeError, JSONDecodeError):
            return

        if not data["Result"]:
            return

        firmware = self.extract_firmware_files(data)

        for item in firmware:
            meta_data = {
                "vendor": "asus",
                "release_date": datetime.strptime(item["ReleaseDate"], "%Y/%m/%d").isoformat(),
                "device_name": device_name,
                "firmware_version": item["Version"],
                "device_class": device_class,
                "file_urls": item["DownloadUrl"]["Global"],
            }
            yield from self.item_pipeline(meta_data)

    @staticmethod
    def extract_firmware_files(data: dict) -> List[dict]:
        with suppress(KeyError):
            for obj in data["Result"]["Obj"]:
                if obj["Name"] == "Firmware":
                    return obj["Files"]
        return []
