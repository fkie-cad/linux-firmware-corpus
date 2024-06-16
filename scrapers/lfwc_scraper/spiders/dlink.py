from datetime import datetime
from typing import Generator, Union

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class DLink(FirmwareSpider):
    handle_httpstatus_list = [404]
    name = "dlink"
    allowed_domains = ["eu.dlink.com", "ftp.dlink.de"]

    start_urls = [
        "https://eu.dlink.com/de/de/for-home/wifi?page=-1&mode=ajax&filters=&categories=&target=products",
        "https://eu.dlink.com/de/de/for-home/cameras?page=-1&mode=ajax&filters=&categories=&target=products",
        "https://eu.dlink.com/de/de/for-home/smart-home?page=-1&mode=ajax&filters=&categories=&target=products",
        "https://eu.dlink.com/de/de/for-home/switches?page=-1&mode=ajax&filters=&categories=&target=products",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": True,
    }

    xpath = {
        "product_names_in_category": '//div[@class="product-item__number"]/text()',
        "detail_pages_in_category": '//div[@class="product-item__number"]/parent::a/@href',
        "detail_latest_revision_name": '//select[@id="supportRevision"]/option[last()]/text()',
        "detail_latest_revision_param": '//select[@id="supportRevision"]/option[last()]/@value',
        "version": '//div[@id="firmware"]//td[@data-table-header="Version"]/text()',
        "date": '//div[@id="firmware"]//td[@data-table-header="Datum"]/text()',
        "download_link": '//div[@id="firmware"]//td[@data-table-header=""]/a/@href',
    }

    device_classes_dict = {
        "dba": "Access Point",
        "dap": "Access Point",
        "dis": "Converter",
        "dmc": "Converter",
        "dge": "PCIe-Networkcard",
        "dwa": "PCIe-Networkcard",
        "dxe": "PCIe-Networkcard",
        "dps": "Redundant Power Supply",
        "dsr": "Router (Business)",
        "dwr": "Router (mobile)",
        "dwm": "Router (mobile)",
        "dsl": "Router (Modem)",
        "covr": "Router (Home)",
        "dir": "Router (Home)",
        "dva": "Router (Home)",
        "go": "Router (Home)",
        "dsp": "Smart Plug",
        "dcs": "Smart Wi-Fi Camera",
        "dsh": "Smart Wi-Fi Camera",
        "des": "Switch",
        "dgs": "Switch",
        "dkvm": "Switch",
        "dqs": "Switch",
        "dxs": "Switch",
        "dem": "Transceiver",
        "dub": "USB Extensions",
        "dnr": "Video Recorder",
        "dwc": "Wireless Controller",
        "dwl": "other",
    }

    def parse(self, response: Response, **_) -> Generator[Request, None, None]:
        names = response.xpath(self.xpath["product_names_in_category"]).extract()
        detail_links = response.xpath(self.xpath["detail_pages_in_category"]).extract()
        for name, detail_link in zip(names, detail_links):
            yield Request(
                url=response.urljoin(detail_link), callback=self.process_detail_page, cb_kwargs=dict(product_name=name)
            )

    def process_detail_page(
        self, response: Response, product_name: str, product_revision: str = ""
    ) -> Generator[Union[Request, FirmwareItem], None, None]:
        if product_revision == "":
            latest_revision_on_page = response.xpath(self.xpath["detail_latest_revision_name"]).extract()
            latest_revision_query_param = response.xpath(self.xpath["detail_latest_revision_param"]).extract()

            if len(latest_revision_on_page + latest_revision_query_param) > 0:
                yield Request(
                    url=response.urljoin(f"?revision={latest_revision_query_param[0]}"),
                    callback=self.process_detail_page,
                    cb_kwargs=dict(product_name=product_name, product_revision=latest_revision_on_page[0]),
                )
                return

        version = response.xpath(self.xpath["version"]).extract()
        release_date = response.xpath(self.xpath["date"]).extract()
        download_link = response.xpath(self.xpath["download_link"]).extract()

        if len(download_link + release_date + version) != 3:
            yield from []
            return

        meta_data = {
            "vendor": "DLink",
            "file_urls": [download_link[0]],
            "device_name": f"{product_name} {product_revision}".strip(),
            "device_class": self.map_device_class(download_link[0]),
            "firmware_version": version[0],
            "release_date": datetime.strptime(release_date[0].strip(), "%d.%m.%Y").strftime("%d-%m-%Y"),
        }

        yield from self.item_pipeline(meta_data)

    @classmethod
    def map_device_class(cls, image_path: str) -> str:
        device_class = "unknown"
        for key, value in cls.device_classes_dict.items():
            if key in image_path.lower():
                device_class = value
                break
        return device_class
