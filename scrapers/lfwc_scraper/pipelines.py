from scrapy.pipelines.files import FilesPipeline


class FirmwarePipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        return request.url.split("/")[-1]


class HpPipeline(FirmwarePipeline):
    pass


class LinksysPipeline(FirmwarePipeline):
    pass


class AvmPipeline(FirmwarePipeline):
    pass


class AsusPipeline(FirmwarePipeline):
    pass
