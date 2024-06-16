from scrapy.http import Request


class FTPRequest(Request):
    pass


class FTPFileRequest(FTPRequest):
    pass


class FTPListRequest(FTPRequest):
    pass
