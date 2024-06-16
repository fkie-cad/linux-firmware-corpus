import os
import re
from contextlib import suppress
from datetime import datetime
from json import loads
from typing import Generator, Union

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_requests import FTPFileRequest, FTPListRequest
from lfwc_scraper.custom_spiders import FTPSpider
from lfwc_scraper.items import FirmwareItem


class AVM(FTPSpider):
    """
    This is the original scraper for ftp://ftp.avm.de. It won't work anymore.

    The FTP service has been shut down since. You can obtain all images from https://download.avm.de
    """

    handle_httpstatus_list = [404]
    name = "avm"
    allowed_domains = ["ftp.avm.de", "avm.de"]
    start_urls = ["ftp://ftp.avm.de/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    filter_eol_products = False

    meta_regex = {
        "device_name": re.compile(r"^(?:Produkt|Controller)\s*:\s+(.*)$", flags=re.MULTILINE | re.IGNORECASE),
        "firmware_version": re.compile(r"^Version\s*:\s+(.*)$", flags=re.MULTILINE | re.IGNORECASE),
        "release_date": re.compile(r"^(?:Release-Datum|Build)\s*:\s+(.*)$", flags=re.MULTILINE | re.IGNORECASE),
    }

    def parse(self, response: Response, **_):
        folder = loads(response.body)

        yield from self.recurse_sub_folders(folder, base_url=response.url)
        yield from self.search_firmware_images(folder, base_url=response.url)

    def parse_metadata_and_download_image(
        self, response: Response, image_path, release_date, **_
    ) -> Generator[Union[Request, FirmwareItem], None, None]:
        info_de_txt = response.body.decode("latin-1")

        if release_date is None:
            release_date = (
                self.meta_regex["release_date"].findall(info_de_txt)[0].strip().replace(".", "-").replace("/", "-")
            )
            # fallback
            year = release_date.split("-")[-1]
            if len(year) == 2:
                # millenium-relative date
                abs_year = "20" + year
                release_date = "-".join(release_date.split("-")[:-1] + [abs_year])
            release_date = datetime.strptime(release_date, "%d-%m-%Y")

        meta_data = {
            "vendor": "AVM",
            "source": "vendor",
            "file_urls": [image_path],
            "device_name": self.meta_regex["device_name"].findall(info_de_txt)[0].strip(),
            "device_class": self.map_device_class(image_path=image_path),
            "firmware_version": self.meta_regex["firmware_version"].findall(info_de_txt)[0].strip().split(" ")[-1],
            "release_date": release_date.isoformat(),
        }

        if self.filter_eol_products:
            product_path = image_path.split("/")[-4]
            product_line = image_path.split("/")[-5]
            yield Request(
                f"https://avm.de/produkte/{product_line}/{product_path}",
                callback=self.verify_support,
                cb_kwargs={"meta_data": meta_data},
            )
        else:
            yield from self.item_pipeline(meta_data)

    def search_firmware_images(self, folder: list, base_url: str) -> Generator[FTPFileRequest, None, None]:
        for image in self._image_file_filter(folder):
            image_path = os.path.join(base_url, image["filename"])
            release_date: datetime | None = None

            date_str = re.sub(r"\s\s+", " ", image["date"])

            date_formats: list[str] = ["%b %d %Y", "%d-%b-%Y %H:%M", "%b %D %H:%M"]
            for fmt in date_formats:
                with suppress(ValueError):
                    release_date = datetime.strptime(date_str, fmt)
                    break
            if release_date is not None and release_date.year == 1900:
                release_date = release_date.replace(year=datetime.now().year)
            info_path = os.path.join(base_url, "info_de.txt")
            yield FTPFileRequest(
                info_path,
                callback=self.parse_metadata_and_download_image,
                cb_kwargs={"image_path": image_path, "release_date": release_date},
            )

    def verify_support(self, response: Response, meta_data: dict, **_):
        if response.status == 200:
            yield from self.item_pipeline(meta_data)

    @staticmethod
    def _folder_filter(entries):
        for entry in entries:
            if any(
                [
                    entry["filetype"] != "d",
                    entry["filename"]
                    in ["..", "archive", "beta", "other", "recover", "belgium", "tools", "switzerland"],
                    entry["linktarget"] is not None,
                ]
            ):
                continue
            yield entry

    @staticmethod
    def _image_file_filter(entries: list):
        for entry in entries:
            if any(
                [
                    entry["filetype"] != "-",
                    not entry["filename"].endswith((".image", ".zip")),
                    entry["linktarget"] is not None,
                ]
            ):
                continue
            yield entry

    @classmethod
    def recurse_sub_folders(cls, folder: list, base_url: str):
        for sub_folder in cls._folder_filter(folder):
            name = sub_folder["filename"]
            recursive_path = f"{os.path.join(base_url, name)}/"
            yield FTPListRequest(recursive_path)

    @staticmethod
    def map_device_class(image_path: str) -> str:
        # /fritzbox/<PRODUCT_PARENT>/<locale>/fritz.os/<image>
        if any(substr in image_path.lower() for substr in ["fritzrepeater", "fritzwlan-repeater"]):
            return "repeater"
        if "fritzwlan-usb" in image_path.lower():
            return "wifi-usb"
        if "fritzpowerline" in image_path.lower():
            return "powerline"
        return "router"
