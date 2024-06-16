from time import sleep

from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager


class FirmwareSpiderMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        settings = cls()
        crawler.signals.connect(settings.spider_opened, signal=signals.spider_opened)
        return settings

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for request in start_requests:
            yield request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class FirmwareDownloaderMiddleware(object):

    def __init__(self):
        options = webdriver.FirefoxOptions()
        service = Service(GeckoDriverManager().install())
        driver_cls = webdriver.Firefox
        options.headless = True  # pyright: ignore
        self.driver = driver_cls(options=options, service=service)  # pyright:ignore
        self.wait = WebDriverWait(self.driver, 15)

    def process_request(self, request, spider):
        if "selenium" not in request.meta:
            return None
        self.driver.get(request.url)

        if "hp" in request.meta:
            body = self.hp_processor()
        else:
            sleep(2)
            body = str.encode(self.driver.page_source)

        return HtmlResponse(self.driver.current_url, body=body, encoding="utf-8", request=request)

    def asus_processor(self):
        try:
            self.wait.until(expected_conditions.presence_of_element_located((By.LINK_TEXT, "DOWNLOAD")))
        except TimeoutException:
            print(
                "No DOWNLOAD Field accessible for {}\nStop processing of {}".format(
                    self.driver.current_url, self.driver.current_url
                )
            )
            raise IgnoreRequest
        finally:
            return str.encode(self.driver.page_source)

    def hp_processor(self):
        self.driver.fullscreen_window()
        self.handle_404()
        self.choose_country()
        self.choose_os()
        self.choose_version()
        self.update_os_version()

        return str.encode(self.driver.page_source)

    def handle_404(self):
        if "Oops!" in self.driver.find_element_by_xpath("//h1").text or "Error 404" in self.driver.page_source:
            print(self.driver.current_url, ": 404 Page Not Found - no firmware to find here")
            raise IgnoreRequest

    def choose_country(self):
        element = self.wait.until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, "Australia")))
        element.click()
        try:
            self.wait.until(expected_conditions.invisibility_of_element_located(element))
        except TimeoutException:
            element.click()
            pass

    def choose_os(self):
        if self.wait.until(expected_conditions.element_to_be_clickable((By.ID, "SelectDiffOS"))):
            self.driver.find_element_by_id("SelectDiffOS").click()
            self.wait.until(expected_conditions.element_to_be_clickable((By.ID, "platform_dd_headerLink"))).click()

            for element in self.driver.find_elements_by_xpath('//ul[@id="platform_dd_list"]/li'):
                if element.text == "OS Independent":
                    element.click()
                    break

    def choose_version(self):
        self.driver.find_element_by_id("versionnew_dd_headerValue").click()
        for element in self.driver.find_elements_by_xpath(
            '//ul[@id="versionnew_dd_list" and @class="dropdown-menu"]/li'
        ):
            if element.text == "OS Independent":
                element.click()
                break

    def update_os_version(self):
        element = self.driver.find_element_by_id("os-update")
        element.click()
        if self.wait.until(expected_conditions.invisibility_of_element_located(element)):
            pass

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

    def spider_closed(self):
        self.driver.quit()
