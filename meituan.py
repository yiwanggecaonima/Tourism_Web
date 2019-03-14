import time

from lxml import etree
import requests
from requests import ConnectionError
import json
import re
import math
import pymongo
import logging
import socks
import socket
# socks.set_default_proxy(socks.PROXY_TYPE_HTTP, '119.129.238.124',4206) #socks全局代理 如果requests或者urllib能用不建议用socks
# socket.socket = socks.socksocket
class MT():

    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',}
        self.proxy = None
        self.client = pymongo.MongoClient('localhost',27017) # mongodb
        self.db = self.client["Meituan"]
        self.logger = logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='./meituan.log',
                    filemode='w') # 日志等级 log文件 格式

        self.base_url = "http://i.meituan.com/xiuxianyule/api/getCommentList?"

    def get_html(self,url,params,count=1):
        if count >4:
            print("Max Count")
            return None
        try:
            if self.proxy:
                r = requests.get(url, headers=self.headers, params=params, proxies=self.proxy, timeout=15)
            else:
                r = requests.get(url, headers=self.headers, params=params, timeout=15)
            print(r.status_code)
            if r.status_code == 200:
                r.encoding = "utf-8"
                return r.text
            else:
                logging.debug('状态码错误 !!!')
                return None
        except ConnectionError as e:
            print(e.args)
            logging.debug('连接错误 !!!')
            return self.get_html(url,params,count+1)
        except Exception as e:
            print(e.args)
            logging.debug("未知错误 !!!")
            return self.get_html(url,params,count+1)

    def get_id(self,url_and_name):
        item = {}
        try:
            ret = re.compile(r'\d+')
            id = re.findall(ret,url_and_name["url"])[0]
            if id:
                item["id"] = id
                item["url"]= url_and_name["url"]
                item["name"]= url_and_name["name"]
                print(item)
                return item
        except TypeError as e:
            print(e.args)
            return None
            
    def get_page(self,id_url_name,count=1):
        if count >3:
            print("Get Page Count")
            return None
        params_dict = {}
        p = {'poiId': id_url_name["id"],
        'offset': 10,
        'pageSize': 10,
        'sortType': 1,
        'mode': 0,
        'starRange': '10,20,30,40,50',
        'tag': '全部'}
        html_doc = self.get_html(self.base_url,p)
        print(html_doc)
        if html_doc:
            try:
                num = json.loads(html_doc)["data"]["commentTagDTOList"]
                if num != []:
                    page = num[0]["count"]
                    page_count = int(math.ceil(int(page)/10))
                    print(page_count)
                    params_dict["page_number"] = page_count
                    params_dict["id"] = id_url_name["id"]
                    params_dict["link"] = id_url_name["url"]
                    params_dict["name"] = id_url_name["name"]
                    return params_dict
            except Exception as e:
                print(e.args)
                logging.debug("未知错误 !!!")
                return self.get_page(id_url_name["id"],count+1)

    def parse_data(self,params_dict):
        for i in range(0,params_dict["page_number"]+1):
            params = {'poiId': params_dict["id"],
                 'offset': 10*i,
                 'pageSize': 10,
                 'sortType': 1,
                 'mode': 0,
                 'starRange': '10,20,30,40,50',
                 'tag': '全部'}
            html_doc = self.get_html(self.base_url,params)
            if html_doc:
                try:
                    datas = json.loads(html_doc)["data"]["commentDTOList"]
                    for data in datas:
                        # print(data)
                        item = {}
                        item["name"] = params_dict["name"]
                        item["id"] = params_dict["id"]
                        item["link"] =  params_dict["link"]
                        item["commentTime"] = data["commentTime"]
                        item["userId"] = data["userId"]
                        item["userLevel"] = data["userLevel"]
                        item["userName"] = data["userName"]
                        item["comment"] = data["comment"]
                        item["star"] = data["star"]
                        print(i," =======",item)
                        if item["comment"] != '':
                            self.insert_mongodb(item)
                        else:
                            continue
                    time.sleep(1)
                except Exception:
                    return None

    def insert_mongodb(self,item):
        if self.db['meituan_comment'].update({"userName":item["userName"]},{"$set":item},True):
            print('save to mongodb', item['userName'])
        else:
            print('No to mongodb',item['userName'])

    def run(self):
        with open("/home/parrot/PycharmProjects/all/meituan.txt","r") as f:
            for data in f.readlines():
                link_and_name= json.loads(data.strip('\n'))
                logging.info(link_and_name["url"])
                # print(link_and_name)
                id_url_name = self.get_id(link_and_name)
                if id_url_name:
                    params_dict =self.get_page(id_url_name)
                    if params_dict:
                        self.parse_data(params_dict)
                    else:
                        continue
                else:
                    continue

if __name__ == '__main__':
    M = MT()
    M.run()

