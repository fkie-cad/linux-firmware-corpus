import re
from datetime import datetime
from typing import Generator, Optional, Tuple

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class ClassIdentifier:
    def __init__(self, shortcuts: tuple):
        self.shortcuts: tuple = shortcuts


class Linksys(FirmwareSpider):
    name = "linksys"

    device_classes = {
        ClassIdentifier(("AM",)): "modem",
        ClassIdentifier(("CIT",)): "phone",
        ClassIdentifier(("EF", "EP", "PPS", "PSU", "WPS")): "printer",
        ClassIdentifier(("DMP", "DMC", "DMR", "DMS", "KWH", "MCC")): "media",
        ClassIdentifier(("DMA",)): "media",
        ClassIdentifier(("LAPN", "LAPAC")): "accesspoint",
        ClassIdentifier(("LCA",)): "ipcam",
        ClassIdentifier(("LMR", "LNR")): "video_recorder",
        ClassIdentifier(("LRT",)): "router",
        ClassIdentifier(("LGS",)): "switch",
        ClassIdentifier(("MR", "EA", "WRT", "E", "BEF", "WKU", "WRK")): "router",
        ClassIdentifier(("M10", "M20")): "accesspoint",
        ClassIdentifier(("PL",)): "powerline",
        ClassIdentifier(("RE", "WRE")): "repeater",
        ClassIdentifier(("SE", "EZX")): "switch",
        ClassIdentifier(("WAP",)): "accesspoint",
        ClassIdentifier(("WET", "WUM", "WES")): "repeater",
        ClassIdentifier(("WHW", "VLP", "MX")): "mesh",
        ClassIdentifier(("WMC", "WVC")): "ipcam",
        ClassIdentifier(("WML",)): "media",
        ClassIdentifier(("X", "AG", "WAG")): "router",
    }

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": True,
    }

    xpath = {
        "device_names": '//li[@class="sitemap-list__item"]/a/text()',
        "support_pages": '//li[@class="sitemap-list__item"]/a/@href',
        "download_page": '//a[contains(@title, "FIRMWARE")]/@href',
        "hardware_version_selectors": '//div[starts-with(@id, "version")]',
    }

    start_urls = ["https://www.linksys.com/sitemap"]

    def parse(self, response: Response, **_) -> Generator[Request, None, None]:

        device_names = response.xpath(self.xpath["device_names"]).extract()
        support_pages = response.xpath(self.xpath["support_pages"]).extract()

        for name_dirty, url in zip(device_names, support_pages):
            yield Request(
                url=response.urljoin(url),
                callback=self.parse_support_page,
                cb_kwargs={"device_name": name_dirty.split(".")[0].strip()},
            )

    def parse_support_page(self, response: Response, device_name: str) -> Optional[Request]:
        download_page = response.xpath(self.xpath["download_page"]).get()
        if not download_page:
            return None
        return Request(
            url=response.urljoin(download_page),
            callback=self.parse_download_page,
            cb_kwargs={"device_name": device_name},
        )

    @classmethod
    def extract_date_and_version(cls, response: Response) -> Tuple[str, str]:
        matches = response.xpath(cls.xpath["date_and_version"]).extract()
        if len(matches) < 2:
            return "", ""

        firmware_version = matches[0].replace("Ver.", "")
        release_date = matches[1].split(" ")[-1].replace("/", "-")
        return firmware_version, release_date

    def parse_download_page(self, response: Response, device_name: str) -> Generator[FirmwareItem, None, None]:
        hw_version_selectors = response.xpath(self.xpath["hardware_version_selectors"])

        for sel in hw_version_selectors:
            hw_version = "ver. 1.0"
            hw_version_dirty = sel.xpath("./@id").get()

            if hw_version_dirty is not None:
                hw_version = f'ver. {hw_version_dirty.replace("version_", "").replace("_", ".")}'

            device_name = f"{device_name} {hw_version}"

            firmware_download_urls = sel.xpath('.//p//a[contains(@href, "firmware")]/@href').extract()
            versions = []
            release_dates = []

            date_finder = re.compile(r".*\:\s*(\d+\/\d+\/\d{4}).*")

            for text in sel.xpath('.//p[contains(text(), "Ver.")]/text()').extract():
                if "Ver." in text:
                    versions += [text.replace("Ver.", "").replace(" ", "")]
                    continue

                dates = date_finder.findall(text)
                if dates:
                    release_dates += [datetime.strptime(dates[0], "%m/%d/%Y").isoformat()]

            for url, version, date in zip(firmware_download_urls, versions, release_dates):
                meta_data = {
                    "vendor": "linksys",
                    "source": "vendor",
                    "file_urls": [url],
                    "device_name": device_name,
                    "device_class": self.map_device_class(device_name),
                    "firmware_version": version,
                    "release_date": date,
                }

                yield from self.item_pipeline(meta_data)

    @classmethod
    def map_device_class(cls, device_name: str) -> str:
        for identifiers, device_class in cls.device_classes.items():
            if device_name.startswith(identifiers.shortcuts):
                return device_class
        return "unknown"
