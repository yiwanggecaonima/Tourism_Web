# coding=utf-8
import json
import logging
import os
import re
import time
import requests
import math
import pymongo

class fzw():

    def __init__(self):
        self.get_link_url = "https://traveldetail.fliggy.com/async/queryItemDetailAjaxInfo.do"
        self.parse_url = "https://traveldetail.fliggy.com/async/queryRateList.do"
        self.cookie = "cna=4CMQFCJ961sCAXFDCsi/YcZ/; hng=CN%7Czh-CN%7CCNY%7C156; dnk=%5Cu4F60%5Cu8111%5Cu5B50%5Cu8FDB%5Cu6C34%5Cu4E8614322389; t=8479bafcf0d1952ad87b3970685ad3a9; tracknick=%5Cu4F60%5Cu8111%5Cu5B50%5Cu8FDB%5Cu6C34%5Cu4E8614322389; _tb_token_=536063d81506b; cookie2=1451a0d6107219a647bd8749bb850ee6; ck1=""; lgc=%5Cu4F60%5Cu8111%5Cu5B50%5Cu8FDB%5Cu6C34%5Cu4E8614322389; otherx=e%3D1%26p%3D*%26s%3D0%26c%3D0%26f%3D0%26g%3D0%26t%3D0; uc1=cookie16=VT5L2FSpNgq6fDudInPRgavC%2BQ%3D%3D&cookie21=W5iHLLyFe3xm&cookie15=W5iHLLyFOGW7aA%3D%3D&existShop=false&pas=0&cookie14=UoTZ5bos%2BLmjkg%3D%3D&tag=8&lng=zh_CN; uc3=vt3=F8dByEvxdCk2Qxs84m4%3D&id2=UUGrdCbj1XPhCQ%3D%3D&nk2=pytjecxC3%2F93WdutYIwejoPFFXY%3D&lg2=UIHiLt3xD8xYTw%3D%3D; _l_g_=Ug%3D%3D; unb=2992790576; cookie1=UIHzmwsRGZPI2P5rNHO2lX0w3R0Kxa2ZZqtR0lsiXMs%3D; login=true; cookie17=UUGrdCbj1XPhCQ%3D%3D; _nk_=%5Cu4F60%5Cu8111%5Cu5B50%5Cu8FDB%5Cu6C34%5Cu4E8614322389; uss=""; csg=8dd3ab7e; skt=79b7454f477b7211; _mw_us_time_=1551925532206; x5sec=7b22617365727665723b32223a226630333964303831363261343632376563393438333039356432383732333330434b575967755146454f437474717a783563444c35514561445449354f5449334f5441314e7a59374d546b3d227d; isg=BCgojyVD4EuQscwAUBq1CGCN-R_6-YwoL3hlluJZZ6OUPcinimQt6zJ8NJVoCEQz; l=bBI9o15uvsDe06HdBOCa5uI8ah79bIRYSuPRwNxvi_5CD18_Yv7OlshFCeJ62j5R_5LB42LjUly9-etew"
        self.client = pymongo.MongoClient("localhost",27017)
        self.db = self.client["FZW"]
        self.logger = self.Mylogger()

    def Mylogger(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)  # Log等级
        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) # 时间格式 可以自定义
        log_path = "./logs/"
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        log_name = log_path + date + '.log'
        logfile = log_name
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.DEBUG)  # 输出log到文件
        formatter = logging.Formatter("%(asctime)s   %(filename)s[line:%(lineno)d]   %(levelname)s: %(message)s") # 文件打印格式
        fh.setFormatter(formatter)
        logger.addHandler(fh) # 初始化
        return logger

    def Headers(self,url, cookie):
        return {'accept': '*/*',
               'accept-encoding': 'gzip, deflate, br',
               'accept-language': 'zh-CN,zh;q=0.9',
               'cookie': cookie,
               'referer': url,
               'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}

    def get_html(self,url, headers=None, param=None):
        try:
            # proxy = {"https": "http://218.59.221.55:4274"}
            r = requests.get(url, headers=headers, params=param, proxies=None,timeout=15)
            if r.status_code == 200:
                return r.text
            return None
        except:
            return None

    def get_sub_link_html(self,url, id):
        headers = self.Headers(url,self.cookie)
        param = {"id": id,  # 这个id从url获取
                 "categoryType": 3}  # 这个参数固定不变
        response = self.get_html(self.get_link_url, headers=headers,param=param)
        return response

    def get_sub_link(self, html, lst, url, count=1):
        if count > 4:
            print('获取link时重试次数达到最大次数>需要重新获取cookie')
            self.logger.warning('获取link时重试次数达到最大次数>需要重新获取cookie')
            return None
        try:
            data_json = json.loads(html)["module"]
        except KeyError as e:
            print("正在重试,因为module不存在")
            return self.get_sub_link(html, lst, url, count + 1)

        try:
            datas = data_json["relatedItems"]["data"]["relatedItems"][0]["relatedTripItems"]
            for data in datas:
                # print(data["itemName"],data["itemId"],"https:" + data["jumpPcUrl"])
                lst.append("https:" + data["jumpPcUrl"])
            return lst
        except KeyError as e:
            print("不存在列表")
            lst.append(url)
            return lst
        except Exception:
            return self.get_sub_link(html, lst, url, count+1)

    def get_pageNums(self, url,id, count=1):
        if count > 3:
            print("获取page时重试次数达到最大次数>需要重新获取cookie")
            self.logger.warning('获取page时重试次数达到最大次数>需要重新获取cookie')
            return None
        headers = self.Headers(url,self.cookie)
        param = {'id': id,
                 'tagId': ':0',
                 'pageNo': 1,
                 'sort': 0,
                 'pageSize': 20}
        response = self.get_html(self.parse_url,headers=headers,param=param)
        if response:
            try:
                datas = json.loads(response)["module"]["rateList"]
                total = datas["total"]
                if total != '0':
                    page_nums = math.ceil(int(total) / 20)
                    return page_nums
            except KeyError as e:
                time.sleep(3)
                self.logger.warning('正在重试 ...')
                print("出现重试 ...")
                return self.get_pageNums(url,id, count+1)

    def parse_data(self, url, id, page_num, name, count=1):
        if count > 4:
            print('获取item时重试次数达到最大次数>需要重新获取cookie')
            self.logger.warning('获取item时重试次数达到最大次数>需要重新获取cookie')
            return None
        headers = self.Headers(url,self.cookie)
        param = {'id': id,
                 'tagId': ':0',
                 'pageNo': page_num,
                 'sort': 0,
                 'pageSize': 20}
        proxy = {'http': 'http://' + '125.121.170.253:4217'}
        try:
            response = self.get_html(self.parse_url,headers=headers,param=param)
            if response:
                datas = json.loads(response)["module"]["rateList"]["rateCellList"]
                self.logger.warning('正在抓取第' + str(page_num) + '页')
                print("==== page ", page_num)
                for data in datas:
                    # print(data)
                    item = {}
                    item["userNick"] = data["userNick"]
                    item["rateDate"] = data["rateDate"]
                    item["rateContent"] = data["rateContent"]
                    item["rateId"] = data["rateId"]
                    item["link"] = url
                    item["name"] = name
                    appendRate = data["appendRate"]
                    item["appendRate"] = appendRate["content"] if appendRate != None else "没有追评"
                    print(item)
                    self.insert_mongodb(item)
                time.sleep(4)
        except Exception as e:
            print(e)
            time.sleep(5)
            self.logger.warning('过于频繁>正在重试 ...')
            print("出现重试")
            return self.parse_data(url, id, page_num, name, count+1)

    def url_to_id(self,url):
        ret = re.compile(r"id=(\d+)")
        idd = re.findall(ret, url)[0]
        return idd

    def insert_mongodb(self,item):
        if self.db['fzw'].update({'rateId': item["rateId"]},{'$set': item},True):
            print('Saved to mongodb ', item['name'])
        else:
            print('No to mongodb',item['name'])

    def run(self):
        with open("/home/parrot/PycharmProjects/all/feizhu.txt", "r") as f:
            for data in f.readlines()[6:]:
                da = json.loads(data.strip('\n'))
                self.logger.warning('HOME URL ' + da["url"])
                print(da["name"], da["url"])
                id = self.url_to_id(da["url"])
                html = self.get_sub_link_html(self.get_link_url,id)
                if html:
                    lst = []
                    url_list = self.get_sub_link(html, lst, da["url"])
                    if url_list:
                        self.logger.warning('所有成员')
                        self.logger.warning(url_list)
                        for url in url_list:
                            self.logger.warning("当前位置: " + url)
                            print("当前位置:", url)
                            idd = self.url_to_id(url)
                            if idd:
                                page_nums = self.get_pageNums(url,idd)
                                if page_nums:
                                    self.logger.warning("一共有:" + str(page_nums) +"页")
                                    print("一共有" + str(page_nums) +"页")
                                    for page_num in range(1, int(page_nums) + 1):
                                        self.parse_data(url, idd, page_num, da["name"])
                            self.logger.warning("finish: " + url)

if __name__ == '__main__':
    F = fzw()
    F.run()

