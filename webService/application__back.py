# encoding : utf-8
# author : xujipm

import tornado.web
import redis
import pymysql
import json
import re
import jieba


class GetWords(tornado.web.RequestHandler):
    """docstring for GetWords"""
    r = redis.Redis(host="104.223.65.181",
                    port="19396",
                    password="xujipm.cpm.redis")

    def get(self):
        iid = self.get_argument("iid", "")
        # self.write(self.getWords(iid))
        # 分词
        data = self.getWords(iid)
        # re.sub("[\s+|+]", " ", " ".join(jieba.cut_for_search(pingjia)))
        temp = re.sub("\|+", " ", data['list']['pingjia'])
        temp = re.sub("\s+", " ", " ".join(jieba.cut_for_search(temp)))
        data['list']['fenci'] = \
            self.ListCount(temp.split(" "))
        data['list']['pingjia'] = \
            self.ListCount(data['list']['pingjia'].split("|"))
        self.write(json.dumps(data))

    def getWords(self, iid):
        rdata = self.r.get("taobao_" + str(iid))
        print("rdata", rdata)
        if (rdata != "")and rdata:
            print("getWordsFromRedis")
            return self.getWordsFromRedis(rdata.decode('utf-8'))
        else:
            print("getWordsFromMysql")
            return self.getWordsFromMysql(iid)

    def getWordsFromRedis(self, rdata):
        rdata = re.sub("'", "\"", rdata)
        # TODO 不知道`\\x01`怎么出现的，需要矫正
        rdata = re.sub("\\\\x01", "", rdata)
        # print(rdata)
        return {"result": "success", "list": json.loads(rdata)}

    def getWordsFromMysql(self, iid):
        conn = pymysql.connect(host="104.223.65.181",
                               user="tbpjuser1",
                               password="asd123",
                               database="taobao_item_pingjia",
                               port=3306,
                               charset="utf8")
        sql = "SELECT `pingjia`,`pingjia_1`,`updating` FROM `taobao_items` " +\
            "WHERE `item_id`='" + str(iid) + "'"
        cursor = conn.cursor()
        result = cursor.execute(sql)
        if result == 0:
            # TODO 需要增加判断是否已经加入到任务中
            print('self.r.get("taobao_" + str(iid))',
                  self.r.get("taobao_" + str(iid)))
            if self.r.get("taobao_" + str(iid)) == b"":
                status = "inactive"
                resultList = {"fenci": "inactive", "pingjia": "inactive"}
            else:
                url = "https://rate.taobao.com/feedRateList.htm?" +\
                    "auctionNumId=" + str(iid) +\
                    "&currentPageNum=1" +\
                    "&callback=jsonp2375&content=0&" +\
                    "orderType=feedbackdate"
                self.r.lpush("taobao_waite_quene", url)
                self.r.set("taobao_" + str(iid), "")
                print('self.r.set(taobao_' + str(iid) + ', "")')
                status = "waite"
                resultList = {"fenci": "waite", "pingjia": "waite"}
        else:
            # `pingjia`,`pingjia_1`,`updating` -> [0:2]
            sqldata = cursor.fetchone()
            resultList = {"fenci": "",
                          "pingjia": sqldata[1].encode('utf-8').decode()}
            if sqldata[2] == 1:
                expire = 60
                status = "waite"
            else:
                expire = 24 * 60 * 60
                status = "success"

        dataDict = {"result": status, "list": resultList}
        self.r.setex("taobao_" + str(iid), dataDict, expire)
        conn.commit()
        conn.close()
        return dataDict

    def ListCount(self, dataList):
        result = {}
        dataSet = set(dataList)
        for litter in dataSet:
            if litter != "":
                result[litter] = dataList.count(litter)
        return result
