import re
from datetime import datetime
from typing import Generator

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class Edimax(FirmwareSpider):
    name = "edimax"
    manufacturer = "edimax"

    start_urls = ["https://www.edimax.com/edimax/download/download/data/edimax/global/download/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    xpath = {
        "option_links": '//select[@class="step1_select_cb drop_select"]/option[not(@disabled)]/@value',
        "device_names": "//select/option[not(@disabled)]/text()",
        "option_links_2": "//select/option[not(@disabled)]/@value",
    }

    def parse(self, response: Response, **_) -> Generator[Request, None, None]:

        solution_links = response.xpath(self.xpath["option_links"]).extract()
        for solution in solution_links:
            yield Request(
                url=response.urljoin(
                    f"/edimax/product/ajax_product_admin/get_catagory_list_cb/2/{solution}/0/show_all/"
                ),
                callback=self.solution_parse,
            )

    def solution_parse(self, response: Response) -> Generator[Request, None, None]:
        category_links = response.xpath(self.xpath["option_links_2"]).extract()
        for category in category_links:
            device_class = category
            yield Request(
                url=response.urljoin(
                    f"/edimax/product/ajax_product_admin/get_product_list_cb/2/{category}/0/show_all/"
                ),
                callback=self.class_parse,
                cb_kwargs={"device_class": device_class},
            )

    def class_parse(self, response: Response, device_class: str) -> Generator[Request, None, None]:
        device_links = response.xpath(self.xpath["option_links_2"]).extract()
        device_names = response.xpath(self.xpath["device_names"]).extract()
        for device_name, device_link in zip(device_names, device_links):
            yield Request(
                url=response.urljoin(
                    f"/edimax/download/ajax_download/get_download_list/2/global/download/{device_link}/{device_link}/3/"
                ),
                callback=self.device_parse,
                cb_kwargs={"device_class": device_class, "device_name": device_name},
            )

    def device_parse(
        self, response: Response, device_class: str, device_name: str
    ) -> Generator[FirmwareItem, None, None]:
        table_row_selectors = response.xpath(
            '//h3[text()="Firmware"]/following-sibling::div[@class="datagrid_tablesorter"][1]//tr'
        )

        date_re = re.compile(r"(\d+\-\d+\-\d+).*")
        version_re = re.compile(r".*\(Version\s?\:?\s?(.*)\).*", flags=re.MULTILINE)

        if not table_row_selectors:
            return

        for row in table_row_selectors[1:]:
            download_link = row.xpath("./td[4]//a/@href").get()
            release_dates_dirty = row.xpath("./td[1]//span/text()").extract()
            info_rows = row.xpath("./td[1]/text()").extract()

            release_date = datetime.strptime("1970-01-01", "%Y-%m-%d").isoformat()
            for date_dirty in release_dates_dirty:
                search_results = date_re.findall(date_dirty)

                if search_results:
                    release_date = datetime.strptime(search_results[0].strip(), "%Y-%m-%d").isoformat()

            firmware_version = "1.0.0"
            for info in info_rows:
                search_results = version_re.findall(info)

                if search_results:
                    firmware_version = search_results[0]

            meta_data = {
                "vendor": "edimax",
                "release_date": release_date,
                "device_name": device_name,
                "firmware_version": firmware_version,
                "device_class": device_class,
                "file_urls": [response.urljoin(download_link)],
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
