# -*- coding: utf-8 -*-
import scrapy


class ExampleSpider(scrapy.Spider):
    name = "tbs"
    allowed_domains = ["taobao.com"]
    start_urls = [
        'https://rate.taobao.com/feedRateList.htm?auctionNumId=532208258584&pageSize=20&currentPageNum=1&callback=tb']

    def parse(self, response):
        filename = response.url.split("/")[-2]
        with open(filename, 'wb') as f:
            f.write(response.body)
        pass
