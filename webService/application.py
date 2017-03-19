# encoding : utf-8
# author : xujipm

import tornado.web
import redis
import pymysql
import json
import re
import jieba


HOST = "127.0.0.1"


class GetWords(tornado.web.RequestHandler):
    """docstring for GetWords"""
    r = redis.Redis(host=HOST,
                    port="19396",
                    password="xujipm.cpm.redis")

    def get(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.set_header('Access-Control-Allow-Origin', '*')
        iid = self.get_argument("iid", "")
        # callback = self.get_argument("callback", "")
        # self.write(self.getWords(iid))
        # 分词
        data = self.getWords(iid)
        # self.write(callback + '({"result":"suces"})')
        self.write(json.dumps(data))
        self.finish()

    def getWords(self, iid):
        rdata = self.r.get("taobao_" + str(iid))
        # print("rdata", rdata)
        if (rdata != "")and rdata:
            # print("getWordsFromRedis")
            return self.getWordsFromRedis(rdata.decode('utf-8'))
        else:
            # print("getWordsFromMysql")
            return self.getWordsFromMysql(iid)

    def getWordsFromRedis(self, rdata):
        rdata = re.sub("'", "\"", rdata)
        # TODO 不知道`\\x01`怎么出现的，需要矫正
        rdata = re.sub("\\\\x01", "", rdata)
        # print(rdata)
        return json.loads(rdata)

    def getWordsFromMysql(self, iid):
        conn = pymysql.connect(host=HOST,
                               user="123",
                               password="123",
                               database="taobao_item_pingjia",
                               port=3306,
                               charset="utf8")
        sql = "SELECT `pingjia_1`,`updating`,`last_update_time` " +\
            "FROM `taobao_items` " +\
            "WHERE `item_id`='" + str(iid) + "'"
        cursor = conn.cursor()
        result = cursor.execute(sql)
        sqldata = cursor.fetchone()
        status = "waite"
        expire = 60

        if result == 0:
            # 数据库没有记录，加入到任务中
            # TODO :
            # 根据 sqldata[2] = last_update_time 判断上次抓取时间，重新加入到队列中
            url = "https://rate.taobao.com/feedRateList.htm?" +\
                "auctionNumId=" + str(iid) +\
                "&currentPageNum=1" +\
                "&callback=jsonp2375&content=0&" +\
                "orderType=feedbackdate"
            self.r.lpush("taobao_waite_quene", url)
            resultList = {"fenci": {"waite": ""}, "pingjia": {"waite": ""}}
            sql = "INSERT INTO `taobao_items` " +\
                "(`item_id`,`updating`) VALUES ('" + str(iid) + "',1)"
            cursor.execute(sql)
        else:
            # `pingjia`,`pingjia_1`,`updating` -> [0:2]
            pingjia = sqldata[0].encode('utf-8').decode()
            temp = re.sub("\|+", " ", pingjia)
            # seg_list = jieba.cut(temp, cut_all=True)  # 全模式
            seg_list = jieba.cut(temp, cut_all=False)  # 精确模式
            # seg_list = jieba.cut_for_search(temp)  # 搜索模式
            fenci = re.sub("\s+", " ", " ".join(seg_list))
            resultList = {"fenci": self.ListCount(fenci.split(" ")),
                          "pingjia": self.ListCount(pingjia.split("|"))}
            if sqldata[1] != 1:
                status = "success"
                expire = 24 * 60 * 60

        dataDict = {"result": status, "list": resultList}
        self.r.setex("taobao_" + str(iid), dataDict, expire)
        conn.commit()
        conn.close()
        return dataDict

    def ListCount(self, dataList):
        result = {}
        dataSet = set(dataList)
        for litter in dataSet:
            num = dataList.count(litter)
            if (litter != "")and(num > 0):
                result[litter] = num
        result = dict(
            sorted(result.items(), key=lambda d: d[1], reverse=True)[:100])
        return result
