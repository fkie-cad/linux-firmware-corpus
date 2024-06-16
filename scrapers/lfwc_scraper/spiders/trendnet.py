import re
from datetime import datetime
from typing import Generator

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class Trendnet(FirmwareSpider):
    name = "trendnet"
    manufacturer = "trendnet"

    start_urls = ["https://www.trendnet.com/support/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    xpath = {
        "product_links": '//option[starts-with(@value,"support-detail.asp")]/@value',
        "device_class_hint": '//h1[@class="g-font-weight-300 mb-0"]/text()',
        "device_name": '//h2[contains(@class, "g-mb-10 g-font-size-18")]/text()',
        "release_dates": "//pre/text()",
        "firmware_links": '//a[contains(@href, "Firmware") or contains(@href, "firmware")]/@href',
        "firmware_filenames": '//a[contains(@href, "Firmware") or contains(@href, "firmware")]/text()',
        "download_folder_hint": '//div[contains(@class, "card-header") and contains(text(), "Firmware")]//parent::*//a[@id="download"]/@data-src[1]',
        "download_folder": '//a[contains(@href, "https://downloads.trendnet.com")]/@href[1]',
    }

    regex = {"firmware_version": re.compile(r".*Firmware(?:\s?\-?[vV]ersion)?\s([\d\.]+).*$", flags=re.MULTILINE)}

    def parse(self, response: Response, **_) -> Generator[Request, None, None]:
        product_support_links = response.xpath(self.xpath["product_links"]).extract()
        for link in product_support_links:
            yield Request(url=response.urljoin(link), callback=self.support_page)

    def support_page(self, response: Response) -> Generator[Request, None, None]:
        device_class_hint = response.xpath(self.xpath["device_class_hint"]).get()

        if not device_class_hint:
            device_class_hint = "unknown"

        device_class = self.map_device_class(device_class_hint)

        device_name_dirty = response.xpath(self.xpath["device_name"]).get()

        if not device_name_dirty:
            return

        device_name_dirty = device_name_dirty.strip().replace("\n", "").replace("\xa0", "")
        device_name = re.sub(r"\s\s+", " ", device_name_dirty)

        download_folder_hint = response.xpath(self.xpath["download_folder_hint"]).get()

        if not download_folder_hint:
            return

        yield Request(
            url=f"{response.urljoin(download_folder_hint)}&button=Continue+with+Download&Continue=yes",
            callback=self.extract_download_folder_hint,
            cb_kwargs={
                "device_name": device_name,
                "device_class": device_class,
            },
            meta={"dont_redirect": True},
        )

    def extract_download_folder_hint(
        self, response: Response, device_name: str, device_class: str
    ) -> Generator[Request, None, None]:
        download_folder_dirty = response.xpath(self.xpath["download_folder"]).get()
        if not download_folder_dirty:
            return
        download_folder_link = "/".join(download_folder_dirty.split("/")[:-1])
        yield Request(
            url=download_folder_link,
            callback=self.directory_listing,
            cb_kwargs={
                "device_name": device_name,
                "device_class": device_class,
            },
        )

    def directory_listing(
        self, response: Response, device_name: str, device_class: str
    ) -> Generator[FirmwareItem, None, None]:
        text_nodes_with_release_date = response.xpath(self.xpath["release_dates"]).extract()

        dates = [
            datetime.strptime(d.strip().split(" ")[0], "%m/%d/%Y").isoformat() for d in text_nodes_with_release_date
        ]

        download_links = response.xpath(self.xpath["firmware_links"]).extract()
        fw_filenames = response.xpath(self.xpath["firmware_filenames"]).extract()

        for fn, link, date in zip(fw_filenames, download_links, dates):
            meta_data = {
                "vendor": "trendnet",
                "release_date": date,
                "device_name": device_name,
                "firmware_version": fn,
                "device_class": device_class,
                "file_urls": [response.urljoin(link)],
            }
            yield from self.item_pipeline(meta_data)

    @staticmethod
    def map_device_class(device_title: str) -> str:
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
        if "camera" in device_title.lower():
            return "ipcam"
        if "phone" in device_title.lower():
            return "phone"
        return "unknown"
