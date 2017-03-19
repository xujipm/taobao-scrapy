# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
import redis
import pymysql
import re
# import jieba
# import time


class TbsPipeline(object):
    '''

    1、将爬取的评价以空格为间隔存进taobao_items中
    2、将单条评价记录存进pingjia中，方便后期分析

    '''

    r = redis.Redis(host="127.0.0.1",
                    port="19396",
                    password="passwd")
    rPipe = r.pipeline()

    exceptWords = ["&hellip;", "评价方未及时做出评价,系统默认好评!", "好评！"]

    def process_item(self, item, spider):
        data = json.loads(item["content"][12:-2])

        # 根据评价中的`from`字段判断宝贝的类型
        # 为空是淘宝，为`b2cMapping`是天猫
        if data['comments'][0]['from'] == "b2cMapping":
            item['shopType'] = "B"
        else:
            item['shopType'] = "C"
        item['itemId'] = data['comments'][0]['auction']['aucNumId']
        item['page'] = data['currentPageNum']

        conn = pymysql.connect(host="127.0.0.1",
                               user="123",
                               password="123",
                               database="taobao_item_pingjia",
                               port=3306,
                               charset="utf8")
        cursor = conn.cursor()

        # 将剩余的评论抓取加入任务
        # TODO: 迁移到任务入口
        print("currentPageNum:", item['page'])
        if item['page'] == 1:
            # 更新`updating`='1'，当前状态是开始抓取
            sql = "UPDATE `taobao_items` SET `updating`='1' where " +\
                "`item_id` ='" + item['itemId'] + "'"
            cursor.execute(sql)
            conn.commit()
            # 将任务放进redis中,min()的作用最多新抓取200页
            for pageNum in range(2, min(data['total'] // 20 + 1, 200)):
                url = "https://rate.taobao.com/feedRateList.htm?" +\
                    "auctionNumId=" + item['itemId'] +\
                    "&currentPageNum=" + str(pageNum) +\
                    "&callback=jsonp2375&content=0&" +\
                    "orderType=feedbackdate"
                self.rPipe.lpush("taobao_waite_quene", url)
                self.rPipe.set("taobao_" + item['itemId'], "")
                print("add page in redis: ", pageNum)
            self.rPipe.execute()

        # # 整页储评价
        # pingjia = ""
        # sql = "INSERT INTO `pingjia` (`item_id`,`rate_id`,`content`," +\
        #     "`comments`,`date`,`from`) VALUES"
        # for i in data['comments']:
        #     pingjia = pingjia + "    " + i['content']
        #     print(i['rateId'], i['date'], i['from'])
        #     sql = sql + "('" + item['itemId'] + "','" + str(i['rateId']) + \
        #         "','" + i['content'] + "','" + json.dumps(i) + "','" + \
        #         i['date'] + "','" + i['from'] + "'),"
        #     # print(sql)
        # cursor.execute(sql[:-1])
        # conn.commit()

        # 分条存储评价
        pingjia = ""
        sql = "INSERT INTO `pingjia` (`item_id`,`rate_id`,`content`," +\
            "`comments`,`date`,`from`) VALUES "
        for i in data['comments']:
            # 如果rateId存在说明后面的都已经抓取过了，直接跳过后面的步骤
            if cursor.execute("select * from `pingjia` where `rate_id` = " +
                              str(i['rateId'])):
                print("ERROR: exist in database")
                pingjia = None
                # 更新`updating`='0'，当前状态是抓取完成状态
                cursor.execute("UPDATE `taobao_items` SET" +
                               " `updating`='0' where " +
                               "`item_id` ='" + item['itemId'] + "'")
                conn.commit()
                break
            pingjia = pingjia + "    " + i['content']
            print(i['rateId'], i['date'], i['from'])
            sql = sql + "('" + item['itemId'] +\
                "','" + str(i['rateId']) + \
                "','" + i['content'] + "','" + "json.dumps(i)" + "','" + \
                i['date'] + "','" + i['from'] + "'),"
            # print(sql)
        if sql != "INSERT INTO `pingjia` (`item_id`,`rate_id`,`content`," +\
                "`comments`,`date`,`from`) VALUES ":
            cursor.execute(sql,)
            conn.commit()

        # 如果已经存在评价记录就直接跳过数据更新流程
        if pingjia is None:
            return item

        # 记录宝贝信息
        pingjia = re.sub("|".join(self.exceptWords), "", pingjia)
        pingjia1 = re.sub("\s+", "|", pingjia)
        # pingjia = re.sub("\s+", " ", " ".join(jieba.cut_for_search(pingjia)))
        pingjia = ""
        # print("pingjia", pingjia, "\npingjia_1", pingjia1)
        if cursor.execute("select * from `taobao_items` where `item_id` = " +
                          item['itemId']):
            sql = "UPDATE `taobao_items` SET `item_pingjiashu`='" +\
                str(data['total']) + "'," +\
                "`last_update_time`=NOW()," +\
                "`update_times`=`update_times`+1," +\
                "`pingjia`=CONCAT('" + pingjia + " ',`pingjia`)," +\
                "`pingjia_1`=CONCAT('" + pingjia1 + "|',`pingjia_1`) " +\
                "where `item_id` ='" + item['itemId'] + "'"
        else:
            sql = "INSERT INTO `taobao_items` (`item_id`, `pingjia`, " +\
                "`pingjia_1`," + "`item_pingjiashu`,`last_update_time`," +\
                " `update_times`) VALUES ('" + item['itemId'] + "','" +\
                pingjia + "','" + pingjia1 + "','" +\
                str(data['total']) + "',NOW(),'1')"
        # print(sql)
        cursor.execute(sql)
        conn.commit()

        # 抓取到最后一页时，更新`updating`='0'，当前状态是抓取完成状态
        if data['total'] // 20 <= data['currentPageNum']:
            sql = "UPDATE `taobao_items` SET `updating`='0' where " +\
                "`item_id` ='" + item['itemId'] + "'"
            cursor.execute(sql)
            conn.commit()

        conn.close()

        # print(item['shopType'], item['itemId'], item['page'], sep=" _ ")
        # print("--------------------------------------")
        return item
