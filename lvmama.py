import time
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach()) # 解决编码问题
from lxml import etree
import requests
from requests.exceptions import ConnectionError
from lxml import etree
import re
import math
import pymongo

class Lmm():
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
        self.client = pymongo.MongoClient('localhost',27017) # mongodb
        self.db = self.client["lvmama"]
        self.proxy = None

    def get_proxy(self):
        headers = {"user-agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60"}
        try:
            res = requests.get(
                "http://...", # 代理api
                headers=headers, timeout=15)
            data = res.text
            res.close()
            ip_port = data.strip("\r\n")
            # print(ip_port)
            if '设置为白名单' in data:
                ret = re.compile(r'请将(.*)设置为白名单')
                ip = re.findall(ret, data)[0]
                print(ip, type(ip))
                white_ip = 'http://=&white=' + ip
                result = requests.get(white_ip, headers=headers, timeout=15)
                if '保存成功' in result.text:
                    print('白名单保存成功')
                    self.get_proxy()
            elif '您的套餐pack传参有误' in data:
                ret = re.compile(r'请检测您现在的(.*)是否在套餐')
                ip = re.findall(ret, data)[0]
                print(ip, type(ip))
                white_ip = 'http://&white=' + ip
                result = requests.get(white_ip, headers=headers, timeout=15)
                if '保存成功' in result.text:
                    print('白名单保存成功')
                    time.sleep(2)
                    self.get_proxy()
            return ip_port
            
        except TimeoutError as e:
            print(e.args)
            time.sleep(1.6)
            return self.get_proxy()
            
        except ConnectionError as e:
            print(e.args)
            time.sleep(2)
            return self.get_proxy()

    def get_params(self, url):
        params_dict = {}
        r = requests.session()
        # url = "http://ticket.lvmama.com/scenic-100417"
        response = r.get(url, headers=self.headers,timeout=15)
        doc_get = etree.HTML(response.text)
        response.close()
        title = doc_get.xpath("//h1/text()")
        title = title[0] if len(title) > 0 else None
        star = doc_get.xpath("//div[@class='titbox']/span[@class='mp_star']/i/text()")
        star = star[0] if len(star) > 0 else None
        link = url
        hei = re.compile(r'\d+')
        if hei != []:
            user_id = re.findall(hei, link)[0]
            count = doc_get.xpath("//*[@id='allCmt']/span/text()")
            count = count[0] if len(count) > 0 else None
            print(count)
            if count is not None:
                ret = re.compile(r'\d+')
                num = re.findall(ret, count)[0]
                t = int(math.ceil(int(num) / 10))
                params_dict["user_id"] = user_id
                params_dict["title"] = title
                params_dict["star"] = star
                params_dict["link"] = link
                params_dict["num"] = num
                params_dict["page_num"] = t
                print(params_dict)
                return params_dict
            else:
                return None

    # data = {'type': 'all',
    # 'currentPage': i,
    # 'totalCount': 23730,
    # 'placeId': 100417,
    # 'productId': None,
    # 'placeIdType': 'PLACE',
    # 'isPicture': None,
    # 'isBest': None,
    # 'isPOI': 'Y',
    # 'isELong': 'N'}
    def get_data(self, params_dict,count=1):
        if count > 3:
            return None
        if params_dict:
            for i in range(1, params_dict["page_num"] + 1):
                data = {'type': 'all',
                        'currentPage': i,
                        'totalCount': params_dict["num"],
                        'placeId': params_dict["user_id"],
                        'productId': None,
                        'placeIdType': 'PLACE',
                        'isPicture': None,
                        'isBest': None,
                        'isPOI': 'Y',
                        'isELong': 'N'}
                # r = requests.session()
                try:
                    if self.proxy:
                        res = requests.post("http://ticket.lvmama.com/vst_front/comment/newPaginationOfComments",
                                        headers=self.headers, proxies=self.proxy, data=data, timeout=15)
                    else:
                        res = requests.post("http://ticket.lvmama.com/vst_front/comment/newPaginationOfComments",
                                            headers=self.headers,data=data, timeout=15)
                    # print(res.text)
                    doc = etree.HTML(res.text)
                    # res.close()
                    li_list = doc.xpath("//div[@class='comment-li']")
                    if li_list != []:
                        for li in li_list:
                            data_dict = {}
                            user_name = li.xpath("./div[@class='com-userinfo']/p/a[1]/text()")
                            user_name = user_name[0] if len(user_name)>0 else None
                            date_time = li.xpath("./div[@class='com-userinfo']/p/em/text()")
                            date_time = date_time[0] if len(date_time) >0 else None
                            user_id = li.xpath(".//div[@class='com-userinfo']/a[@class='fr com-enjoy']/@id")
                            user_id = user_id[0].split('all_')[-1] if len(user_id) >0 else None
                            content = li.xpath("./div[@class='ufeed-content']/text()")
                            content = ''.join(content).replace('\r','').replace('\n', '').replace('\t', '').replace(' ', '')
                            data_dict["user_name"] = user_name
                            data_dict["user_id"] = user_id
                            data_dict["date_time"] = date_time
                            data_dict["title"] = params_dict["title"]
                            data_dict["star"] = params_dict["star"]
                            data_dict["link"] = params_dict["link"]
                            data_dict["content"] = content
                            print(i,data_dict)
                            self.insert_mongodb(data_dict)
                        time.sleep(0.5)

                except ConnectionError as e:
                    print(e.args)
                    return self.get_data(params_dict,count+1)
                except Exception as e:
                    print(e.args)
                    time.sleep(1.5)
                    self.proxy =  {'http':'http://' + self.get_proxy()}
                    print(self.proxy)
                    return self.get_data(params_dict,count+1)

    def insert_mongodb(self,item):
        # if self.db["Lmm"].update({"user_id":item["user_id"]},{"$set":item},True):
        if self.db["Lmm"].insert(item):
            print("save to mongodb", item['user_name'])
        else:
            print("No mongodb",item["user_name"])

    def run(self):
        with open("/home/parrot/PycharmProjects/all/lvmama.txt", "r") as file:
            for data in file.readlines():
                url = data.strip('\n')
                params_dict = self.get_params(url)
                self.get_data(params_dict)


if __name__ == '__main__':
    L = Lmm()
    L.run()
    
# 注意这是js翻页
"javascript:Comment.newLoadPaginationOfComment({type:'all',currentPage:2,totalCount:'11692',placeId:'120604',productId:'',placeIdType:'PLACE',isPicture:'',isBest:'',isPOI:'Y',isELong:'N'});"
