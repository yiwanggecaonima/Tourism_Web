# 代码写的很机械 很不健壮 后期更改
import time
from lxml import etree
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
import requests
import json
import re
import math
import pymongo

class Qnr():
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
        self.client = pymongo.MongoClient('localhost',27017)
        self.db = self.client["Qnr"]
        
    def get_params(self,url):
        params_dict = {}
        # url = "http://piao.qunar.com/ticket/detail_13628.html#from=mps_search_suggest"
        res = requests.get(url,headers=self.headers)
        # print(res.text)
        doc = etree.HTML(res.text)
        ret = re.compile(r'\d+')
        id = re.findall(ret,url)[0]
        print(id)
        title = doc.xpath("//div[@class='mp-description-detail']/div[@class='mp-description-view']/span[@class='mp-description-name']/text()")
        title = ''.join(title) if len(title) >0 else None
        sightId = doc.xpath("//*[@id='mp-tickets']/@data-sightid")
        sightId = sightId[0] if len(sightId) >0 else None
        count = doc.xpath("//div[@class='mp-comments-number']/span[@id='commentsTotalNum']/text()")
        count = count[0] if len(count) > 0 else None
        params_dict["title"] = title
        params_dict["link"] = url
        params_dict["sightId"] = sightId
        params_dict["count"] = count
        return params_dict
        
    def get_data(self,params_dict):
        for t in range(1,int(math.ceil(int(params_dict["count"])/100)+1)):
            p = {'sightId':params_dict["sightId"],
            'index': t,
            'page': t,
            'pageSize': 100,
            'tagType': 0}
            r = requests.session()
            url = "http://piao.qunar.com/ticket/detailLight/sightCommentList.json"
            response = r.get(url,headers=self.headers,params = p)
            datas = json.loads(response.text)
            score = datas["data"]["score"]
            print(len(datas["data"]["commentList"]))
            for i in datas["data"]["commentList"]:
                i["score"] = score
                i["title"] = params_dict["title"]
                i["link"] = params_dict["link"]
                if i["imgs"]:
                    del i["imgs"]
                print(i,'==========',t)
                self.insert_mongodb(dict(i))
            time.sleep(1.5)

    def insert_mongodb(self,item):
        # if self.db["Lmm"].update({"user_id":item["user_id"]},{"$set":item},True):
        if self.db["qunaer"].insert(item):
            print("save to mongodb", item['title'])
        else:
            print("No mongodb",item["title"])
            
    def run(self):
        with open("/home/parrot/PycharmProjects/all/qunaer.txt","r") as f:
            for data in f.readlines()[120:]:
                data_dict = json.loads(data.strip('\n'))
                params_dict = self.get_params(data_dict["link"])
                self.get_data(params_dict)

if __name__ == '__main__':
    Q = Qnr()
    Q.run()
    
    
    
# print(response.text)
# ret = re.compile(r'\d+')
# id = re.findall(ret,url)[0]
# print(id)
# doc = etree.HTML(response.text)
# lis = doc.xpath("//div[@id='searchResultContainer']/ul/li")
# for li in lis:
#     item = {}
#     item["user_name"] = li.xpath("./div[@class='mp-comments-title']/span[@class='mp-comments-username']/text()")[0]
#     item["date_time"] = li.xpath("./div[@class='mp-comments-title']/span[@class='mp-comments-time']/text()")[0]
#     item["content"] = ''.join(li.xpath("./p[@class='mp-comments-desc']/text()"))
#     print(item)
