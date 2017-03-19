# -*- coding: utf-8 -*-
import scrapy
import redis
import time
from scrapy.http import Request
from tbs.items import TbsItem


HOST = "127.0.0.1"
PORT = "19396"
PASSWD = "passwd"


class TaobaoSpider(scrapy.Spider):
    name = "taobao"
    allowed_domains = ["taobao.com"]
    # start_urls = ['https://taobao.com/']
    r = redis.Redis(host=HOST, port=PORT,
                    password=PASSWD)

    def start_requests(self):
        return [Request(self.GetUrl(), callback=self.parse, dont_filter=False)]

    def parse(self, response):
        if self.Banned(response):
            yield Request(url=response.url,
                          meta={"change_proxy": True},
                          callback=self.parse)
        else:
            pass
            yield TbsItem(content=response.text)
            print(self.r.rpoplpush("taobao_inactive_quene",
                                   "taobao_success_quene").decode())
            yield Request(self.GetUrl(),
                          callback=self.parse,
                          dont_filter=False)
            # return [Request(self.GetUrl(), callback=self.parse,
            # dont_filter=True)]

    def GetUrl(self):
        while self.r.llen("taobao_waite_quene") == 0:
            time.sleep(5)
        # TODO 需要确定redis是否线程安全
        url = self.r.rpoplpush("taobao_waite_quene",
                               "taobao_inactive_quene").decode()
        return url

    def Banned(self, response):
        # 判断是否被ban，如果被ban返回Ture，反之返回False
        # TODO 判断是否被ban
        return False
