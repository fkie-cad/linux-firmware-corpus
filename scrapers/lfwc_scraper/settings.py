# Scrapy settings for firmware project

BOT_NAME = "lfwc_scraper"

SPIDER_MODULES = ["lfwc_scraper.spiders"]
NEWSPIDER_MODULE = "lfwc_scraper.spiders"

FILES_STORE = "firmware_files/"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True
DOWNLOAD_TIMEOUT = 320
LOG_LEVEL = "DEBUG"
FTP_USER = "anonymous"
FTP_PASSWORD = "guest"

DOWNLOAD_HANDLERS = {"ftp": "lfwc_scraper.handlers.FTPHandler"}

DOWNLOADER_MIDDLEWARES = {
    "lfwc_scraper.middlewares.FirmwareDownloaderMiddleware": 543,
}

ITEM_PIPELINES = {
    "lfwc_scraper.pipelines.HpPipeline": 300,
    "lfwc_scraper.pipelines.AsusPipeline": 300,
    "lfwc_scraper.pipelines.AvmPipeline": 1,
    "lfwc_scraper.pipelines.LinksysPipeline": 1,
}
