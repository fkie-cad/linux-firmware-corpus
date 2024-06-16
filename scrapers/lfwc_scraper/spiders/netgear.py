import json
import re
from datetime import datetime
from typing import Generator

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class Netgear(FirmwareSpider):
    name = "netgear"
    manufacturer = "NETGEAR"

    start_urls = ["https://www.netgear.de/system/supportModels.json"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 10,
        "CONCURRENT_ITEMS": 10,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    xpath = {
        "get_kb_article": '//h1[contains(text(), "Firmware")]/parent::a/parent::div/div[@class="accordion-content"]//a[contains(@href, "kb.netgear.com")]/@href',
        "get_download_link": '//h1[contains(text(), "Firmware")]/parent::a/parent::div/div[@class="accordion-content"]/div[@class="links"]/a/@href',
        "get_firmware_text": '//h1[contains(text(), "Firmware")]',
        "get_release_date": '//p[@class="last-updated"]/text()',
    }

    regex = {"firmware_version": re.compile(r".*Firmware(?:\s?\-?[vV]ersion)?\s([\d\.]+).*$", flags=re.MULTILINE)}

    def parse(self, response: Response, **kwargs) -> Generator[Request, None, None]:
        all_products = json.loads(response.text)
        for product in all_products:
            device_class = self.map_device_class(product["title"])
            if device_class == "unknown" or product["external"] != "":
                continue
            support_url = response.urljoin(product["url"])
            device_name = product["model"]
            yield Request(
                url=support_url,
                callback=self.consult_support_pages,
                cb_kwargs={
                    "device_name": device_name,
                    "device_class": device_class,
                },
                meta={"selenium": True},  # required because the xpath queries need a properly built DOM tree via JS
            )

    def consult_support_pages(
        self, response: Response, device_name: str, device_class: str
    ) -> Generator[Request | FirmwareItem, None, None]:
        fw_text_selectors = response.xpath(self.xpath["get_firmware_text"])

        for sel in fw_text_selectors:
            dirty_firmware_version = sel.xpath("./text()").get()
            content_sel = sel.xpath('./parent::a/parent::div/div[@class="accordion-content"]')
            download_link = content_sel.xpath('./div[@class="links"]/a/@href').get()
            kb_article_link = content_sel.xpath('.//a[contains(@href, "kb.netgear.com")]/@href').get()
            firmware_version = self.regex["firmware_version"].findall(dirty_firmware_version)
            if len(firmware_version) == 1:
                firmware_version = firmware_version[0]
            else:
                firmware_version = "0.0.0.0"
            if kb_article_link is not None:
                yield Request(
                    url=kb_article_link,
                    callback=self.parse_kb_article,
                    cb_kwargs={
                        "firmware_version": firmware_version,
                        "download_link": download_link,
                        "device_name": device_name,
                        "device_class": device_class,
                    },
                )
            else:
                meta_data = {
                    "vendor": "netgear",
                    "release_date": datetime.strptime("01-01-1970", "%m-%d-%Y").isoformat(),
                    "device_name": device_name,
                    "firmware_version": firmware_version,
                    "device_class": device_class,
                    "file_urls": [download_link.strip()],
                }
                yield from self.item_pipeline(meta_data)

    def parse_kb_article(
        self, response: Response, device_name: str, firmware_version: str, download_link: str, device_class: str
    ) -> Generator[FirmwareItem, None, None]:

        dirty_release_date = response.xpath(self.xpath["get_release_date"]).get()

        release_date = dirty_release_date.split(":")[-1].strip().replace("/", "-")

        meta_data = {
            "vendor": "netgear",
            "release_date": datetime.strptime(release_date, "%m-%d-%Y").isoformat(),
            "device_name": device_name,
            "firmware_version": firmware_version,
            "device_class": device_class,
            "file_urls": [download_link.strip()],
        }
        yield from self.item_pipeline(meta_data)

    @staticmethod
    def map_device_class(device_title: str) -> str:
        if any(substr in device_title.lower() for substr in ["usb", "unmanaged"]):
            return "unknown"
        if "switch" in device_title.lower():
            return "switch"
        if "access" in device_title.lower():
            return "accesspoint"
        if "repeater" in device_title.lower():
            return "repeater"
        if "powerline" in device_title.lower():
            return "powerline"
        if "router" in device_title.lower():
            return "router"
        if "modem" in device_title.lower():
            return "modem"
        if "mesh" in device_title.lower():
            return "mesh"
        return "unknown"
