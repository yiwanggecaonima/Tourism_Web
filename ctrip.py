# 代码很一般 没有很好的封装函数 出现很多多余代码
# 如果需要改动自行动手 不动也行 当前可以跑通 未来不可知
import random
import re
import time
import requests
from lxml import etree
import requests
from requests.exceptions import ConnectTimeout
import pymongo
import urllib.request
from urllib.error import URLError

class Ctrip():

    def __init__(self):
        self.proxy = None
        self.client = pymongo.MongoClient('localhost',27017) # mongodb
        self.db = self.client['ctrip']
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
        
    def get_proxy(self):
        # if count >4:
        #     return None
        try:
            response = requests.get(
                "http://webapi.http...", # 代理ip api
                headers=self.headers,timeout=15)
            data = response.text
            response.close()
            ip_port = data.strip("\r\n")
            print(ip_port)
            if '设置为白名单' in data:
                ret = re.compile(r'请将(.*)设置为白名单')
                ip = re.findall(ret, data)[0]
                print(ip, type(ip))
                white_ip = 'http://web.http...&white=' + ip
                result = requests.get(white_ip, headers=self.headers, timeout=15)
                if '保存成功' in result.text:
                    print('白名单保存成功')
                    return self.get_proxy()
            elif '您的套餐pack传参有误' in data:
                ret = re.compile(r'请检测您现在的(.*)是否在套餐')
                ip = re.findall(ret, data)[0]
                print(ip, type(ip))
                white_ip = 'http://web.http...&white=' + ip
                result = requests.get(white_ip, headers=self.headers, timeout=15)
                if '保存成功' in result.text:
                    print('白名单保存成功')
                    return self.get_proxy()
            return ip_port
        except ConnectionError as e:
            print(e.args)
            return None
        except Exception as e:
            print(e.args)
            return self.get_proxy()

    def get_Param(self,url,c=1):
        if c>2: # 重试次数
            return None
        r = requests.session() # 建立会话 用于保持cookie
        # url = "http://you.ctrip.com/sight/foshan207/23210.html#ctm_ref=www_hp_bs_lst"
        try:
            if self.proxy:
                response = r.get(url.strip('\n'),headers=self.headers,proxies=self.proxy,timeout=15)
            else:
                response = r.get(url.strip('\n'), headers=self.headers,timeout=15)
            print(response.status_code)
            if "请完成验证后继续访问" in response.text:
                proxy = self.get_proxy()
                self.proxy = {'http':'http://' + proxy}
                print(self.proxy)
                return self.get_Param(url)
        except ConnectTimeout as e:
            print(e.args)
            proxy = self.get_proxy()
            self.proxy = {'http': 'http://' + proxy}
            print(self.proxy)
            return self.get_Param(url)
        except Exception as e:
            print(e.args)
            proxy = self.get_proxy()
            self.proxy = {'http': 'http://' + proxy}
            print(self.proxy)
            return self.get_Param(url)
        doc = etree.HTML(response.text) # xpath解析 css也可以 bs4也没问题  pyquery更好 牛逼一点全用re也ojbk
        param_item = {}
        page_num = doc.xpath("//div[@class='ttd_pager cf']/div/span/b/text()")
        param_item['page_num'] = page_num[0] if len(page_num) > 0 else None
        districtId = doc.xpath("//*[@id='ctmdistrict']/@value")
        param_item['districtId'] = districtId[0] if len(districtId) > 0 else None
        resourceId = doc.xpath("//*[@id='wentClickID']/@data-cat")
        param_item['resourceId'] = resourceId[0] if len(resourceId) > 0 else None
        poiID = doc.xpath("//*[@id='vacationgrouptour']/@data-arrivecityid")
        param_item['poiID'] = poiID[0] if len(poiID) > 0 else None
        province = doc.xpath("//div[@class='breadbar_v1 cf']/ul/li[4]/a/text()")
        param_item['province'] = province[0] if len(province) > 0 else None
        title = doc.xpath("//h1/a/text()")
        param_item['title'] = title[0] if len(title) > 0 else None
        param_item['href'] = url.strip('\n')
        print(param_item)
        if param_item['title'] is None:
            proxy = self.get_proxy()
            self.proxy = {'http': 'http://' + proxy}
            print(self.proxy)
            return self.get_Param(url,c+1)
        return param_item

    def ajax_post(self,param_item,count=1):
        if count > 4: # 同上
            return None
        try:
            if param_item['page_num'] is None:
                data = {'poiID': param_item['poiID'],
                        'districtId': param_item['districtId'],
                        # 'districtEName': 'Foshan',
                        # 'order': 3.0,
                        # 'star': 0.0,
                        # 'tourist': 0.0,
                        'pagenow': 1,
                        'resourceId': param_item['resourceId'],
                        'resourcetype': 2, }
                r = requests.session()
                res = r.post("http://you.ctrip.com/destinationsite/TTDSecond/SharedView/AsynCommentView",
                             headers=self.headers, data=data,timeout=15)
                # print(res.text)
                post_doc = etree.HTML(res.text)
                divs = post_doc.xpath("//div[@class='comment_ctrip']/div[@class='comment_single']")
                for div in divs:
                    ctrip_item = {}
                    ctrip_item['User_name'] = div.xpath("./div[@class='userimg']/span/a/text()")[0]
                    ctrip_item['User_id'] = div.xpath("./ul/li[@class='from_link']/span[@class='f_right']/span/a/@data-id")[0]
                    ctrip_item['Date_time'] = \
                    div.xpath("./ul/li[@class='from_link']/span[@class='f_left']/span[@class='time_line']/em/text()")[0]
                    ctrip_item['Comment'] = ''.join(div.xpath("./ul/li[@class='main_con']/span/text()")).replace('\r','').replace('\n', '').replace('\t', '')
                    all_qi = ''.join(div.xpath("./ul/li[@class='title cf']/span[@class='f_left']/span[@class='sblockline']/text()")).replace('\r','').replace('\n', '').replace('\t', '').replace(' ', '')
                    # ctrip_item['all_qi'] = all_qi
                    if all_qi:
                        ret = re.compile(r'景色：(.*?)\u2003趣味：(.*?)\u2003性价比：(.*?)\u2003')
                        jqx = re.findall(ret, all_qi)
                        # print(jqx)
                        if len(jqx) > 0:
                            ctrip_item['Scenery'] = jqx[0][0]
                            ctrip_item['Interest'] = jqx[0][1]
                            ctrip_item['Cost'] = jqx[0][2]
                    ctrip_item['Province'] = param_item['province']
                    ctrip_item['Scenic'] = param_item['title']
                    ctrip_item['href'] = param_item['href']
                    print(ctrip_item)
                    self.insert_mongo(ctrip_item)
                time.sleep(random.uniform(2,7))
            # 对于所有页面来说 如果超过302页 后面的就取不到了  分两种情况
            elif int(param_item['page_num']) < 302: # 这是第一种情况
                for page in range(1,int(param_item['page_num'])+1):
                    data = {'poiID': param_item['poiID'],
                    'districtId': param_item['districtId'],
                    # 'districtEName': 'Foshan',
                    # 'order': 3.0,
                    # 'star': 0.0,
                    # 'tourist': 0.0,
                    'pagenow': page,
                    'resourceId': param_item['resourceId'],
                    'resourcetype': 2,}
                    r = requests.session()
                    if self.proxy:
                        try:
                            res =r.post("http://you.ctrip.com/destinationsite/TTDSecond/SharedView/AsynCommentView",headers=self.headers,proxies=self.proxy,data=data,timeout=20)
                            if res.status_code == 200:
                                post_doc = etree.HTML(res.text)
                                divs = post_doc.xpath("//div[@class='comment_ctrip']/div[@class='comment_single']")
                                if len(divs) > 0 :
                                    for div in divs:
                                        ctrip_item = {}
                                        ctrip_item['User_name'] = div.xpath("./div[@class='userimg']/span/a/text()")[0]
                                        ctrip_item['User_id'] = \
                                        div.xpath("./ul/li[@class='from_link']/span[@class='f_right']/span/a/@data-id")[0]
                                        ctrip_item['Date_time'] = div.xpath("./ul/li[@class='from_link']/span[@class='f_left']/span[@class='time_line']/em/text()")[0]
                                        ctrip_item['Comment'] = ''.join(div.xpath("./ul/li[@class='main_con']/span/text()")).replace('\r', '').replace('\n','').replace('\t', '')
                                        all_qi = ''.join(div.xpath("./ul/li[@class='title cf']/span[@class='f_left']/span[@class='sblockline']/text()")).replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '')
                                        # ctrip_item['all_qi'] = all_qi
                                        if all_qi:
                                            ret = re.compile(r'景色：(.*?)\u2003趣味：(.*?)\u2003性价比：(.*?)\u2003')
                                            jqx = re.findall(ret, all_qi)
                                            # print(jqx)
                                            if len(jqx) > 0:
                                                ctrip_item['Scenery'] = jqx[0][0]
                                                ctrip_item['Interest'] = jqx[0][1]
                                                ctrip_item['Cost'] = jqx[0][2]
                                        ctrip_item['Province'] = param_item['province']
                                        ctrip_item['Scenic'] = param_item['title']
                                        ctrip_item['href'] = param_item['href']
                                        print(ctrip_item, '-----------', page)
                                        self.insert_mongo(ctrip_item)
                                    time.sleep(random.uniform(0.5, 1.5))
                                else:
                                    proxy = self.get_proxy()
                                    self.proxy = {'http': 'http://' + proxy}
                                    print(self.proxy)
                                    return self.ajax_post(param_item)
                            else:
                                proxy = self.get_proxy()
                                self.proxy = {'http': 'http://' + proxy}
                                print(self.proxy)
                                return self.ajax_post(param_item)
                        except ConnectionError as e:
                            print(e.args)
                            return self.ajax_post(param_item,count+1)
                    else:
                        try:
                            res =r.post("http://you.ctrip.com/destinationsite/TTDSecond/SharedView/AsynCommentView",headers=self.headers, data=data, timeout=20)
                            if res.status_code == 200:
                                # print(res.text)
                                post_doc = etree.HTML(res.text)
                                divs = post_doc.xpath("//div[@class='comment_ctrip']/div[@class='comment_single']")
                                if len(divs) > 0:
                                    for div in divs:
                                        ctrip_item = {}
                                        ctrip_item['User_name'] = div.xpath("./div[@class='userimg']/span/a/text()")[0]
                                        ctrip_item['User_id'] = \
                                        div.xpath("./ul/li[@class='from_link']/span[@class='f_right']/span/a/@data-id")[0]
                                        ctrip_item['Date_time'] = div.xpath("./ul/li[@class='from_link']/span[@class='f_left']/span[@class='time_line']/em/text()")[0]
                                        ctrip_item['Comment'] = ''.join(div.xpath("./ul/li[@class='main_con']/span/text()")).replace('\r', '').replace('\n','').replace('\t', '')
                                        all_qi = ''.join(div.xpath("./ul/li[@class='title cf']/span[@class='f_left']/span[@class='sblockline']/text()")).replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '')
                                        # ctrip_item['all_qi'] = all_qi
                                        if all_qi:
                                            ret = re.compile(r'景色：(.*?)\u2003趣味：(.*?)\u2003性价比：(.*?)\u2003')
                                            jqx = re.findall(ret, all_qi)
                                            # print(jqx)
                                            if len(jqx) > 0:
                                                ctrip_item['Scenery'] = jqx[0][0]
                                                ctrip_item['Interest'] = jqx[0][1]
                                                ctrip_item['Cost'] = jqx[0][2]
                                        ctrip_item['Province'] = param_item['province']
                                        ctrip_item['Scenic'] = param_item['title']
                                        ctrip_item['href'] = param_item['href']
                                        print(ctrip_item, '-----------', page)
                                        self.insert_mongo(ctrip_item)
                                    time.sleep(random.uniform(1,4))
                                else:
                                    proxy = self.get_proxy()
                                    self.proxy = {'http': 'http://' + proxy}
                                    print(self.proxy)
                                    return self.ajax_post(param_item)
                            else:
                                proxy = self.get_proxy()
                                self.proxy = {'http': 'http://' + proxy}
                                print(self.proxy)
                                return self.ajax_post(param_item)
                        except ConnectionError as e:
                            print(e.args)
                            return self.ajax_post(param_item, count + 1)
                        except Exception:
                            proxy = self.get_proxy()
                            self.proxy = {'http': 'http://' + proxy}
                            print(self.proxy)
                            return self.ajax_post(param_item)
                    print(res.status_code)
                    if res.status_code == '404':
                        proxy = self.get_proxy()
                        self.proxy = {'http': 'http://' + proxy}
                        print(self.proxy)
                        return self.ajax_post(param_item)
            else: # 这是第二种情况
                for page in range(1,302):
                    data = {'poiID': param_item['poiID'],
                    'districtId': param_item['districtId'],
                    # 'districtEName': 'Foshan',
                    # 'order': 3.0,
                    # 'star': 0.0,
                    # 'tourist': 0.0,
                    'pagenow': page,
                    'resourceId': param_item['resourceId'],
                    'resourcetype': 2,}
                    r = requests.session()
                    if self.proxy:
                        try:
                            res =r.post("http://you.ctrip.com/destinationsite/TTDSecond/SharedView/AsynCommentView",headers=self.headers,proxies=self.proxy,data=data,timeout=20)
                            if res.status_code == 200:
                                post_doc = etree.HTML(res.text)
                                divs = post_doc.xpath("//div[@class='comment_ctrip']/div[@class='comment_single']")
                                if len(divs) > 0:
                                    for div in divs:
                                        ctrip_item = {}
                                        ctrip_item['User_name'] = div.xpath("./div[@class='userimg']/span/a/text()")[0]
                                        ctrip_item['User_id'] = div.xpath("./ul/li[@class='from_link']/span[@class='f_right']/span/a/@data-id")[0]
                                        ctrip_item['Date_time'] = div.xpath("./ul/li[@class='from_link']/span[@class='f_left']/span[@class='time_line']/em/text()")[0]
                                        ctrip_item['Comment'] = ''.join(div.xpath("./ul/li[@class='main_con']/span/text()")).replace('\r', '').replace('\n','').replace('\t', '')
                                        all_qi = ''.join(div.xpath("./ul/li[@class='title cf']/span[@class='f_left']/span[@class='sblockline']/text()")).replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '')
                                        # ctrip_item['all_qi'] = all_qi
                                        if all_qi:
                                            ret = re.compile(r'景色：(.*?)\u2003趣味：(.*?)\u2003性价比：(.*?)\u2003')
                                            jqx = re.findall(ret, all_qi)
                                            # print(jqx)
                                            if len(jqx) > 0:
                                                ctrip_item['Scenery'] = jqx[0][0]
                                                ctrip_item['Interest'] = jqx[0][1]
                                                ctrip_item['Cost'] = jqx[0][2]
                                        ctrip_item['Province'] = param_item['province']
                                        ctrip_item['Scenic'] = param_item['title']
                                        ctrip_item['href'] = param_item['href']
                                        print(ctrip_item, '-----------', page)
                                        self.insert_mongo(ctrip_item)
                                    time.sleep(random.uniform(0.5,1))
                                else:
                                    proxy = self.get_proxy()
                                    self.proxy = {'http': 'http://' + proxy}
                                    print(self.proxy)
                                    return self.ajax_post(param_item)
                            else:
                                proxy = self.get_proxy()
                                self.proxy = {'http': 'http://' + proxy}
                                print(self.proxy)
                                return self.ajax_post(param_item)
                        except ConnectionError as e:
                            print(e.args)
                            return self.ajax_post(param_item,count+1)
                    else: 
                        try:
                            res =r.post("http://you.ctrip.com/destinationsite/TTDSecond/SharedView/AsynCommentView",headers=self.headers, data=data, timeout=20)
                            if res.status_code == 200:
                                # print(res.text)
                                post_doc = etree.HTML(res.text)
                                divs = post_doc.xpath("//div[@class='comment_ctrip']/div[@class='comment_single']")
                                if len(divs) > 0:
                                    for div in divs:
                                        ctrip_item = {}
                                        ctrip_item['User_name'] = div.xpath("./div[@class='userimg']/span/a/text()")[0]
                                        ctrip_item['User_id'] = \
                                        div.xpath("./ul/li[@class='from_link']/span[@class='f_right']/span/a/@data-id")[0]
                                        ctrip_item['Date_time'] = div.xpath("./ul/li[@class='from_link']/span[@class='f_left']/span[@class='time_line']/em/text()")[0]
                                        ctrip_item['Comment'] = ''.join(div.xpath("./ul/li[@class='main_con']/span/text()")).replace('\r', '').replace('\n','').replace('\t', '')
                                        all_qi = ''.join(div.xpath("./ul/li[@class='title cf']/span[@class='f_left']/span[@class='sblockline']/text()")).replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '')
                                        # ctrip_item['all_qi'] = all_qi
                                        if all_qi:
                                            ret = re.compile(r'景色：(.*?)\u2003趣味：(.*?)\u2003性价比：(.*?)\u2003')
                                            jqx = re.findall(ret, all_qi)
                                            # print(jqx)
                                            if len(jqx) > 0:
                                                ctrip_item['Scenery'] = jqx[0][0]
                                                ctrip_item['Interest'] = jqx[0][1]
                                                ctrip_item['Cost'] = jqx[0][2]
                                        ctrip_item['Province'] = param_item['province']
                                        ctrip_item['Scenic'] = param_item['title']
                                        ctrip_item['href'] = param_item['href']
                                        print(page,'\t',ctrip_item, '-----------')
                                        self.insert_mongo(ctrip_item)
                                    time.sleep(random.uniform(1,2))
                                else:
                                    proxy = self.get_proxy()
                                    self.proxy = {'http': 'http://' + proxy}
                                    print(self.proxy)
                                    return self.ajax_post(param_item)
                            else:
                                proxy = self.get_proxy()
                                self.proxy = {'http': 'http://' + proxy}
                                print(self.proxy)
                                return self.ajax_post(param_item)
                        except ConnectionError as e:
                            print(e.args)
                            return self.ajax_post(param_item, count + 1)
                        except Exception:
                            proxy = self.get_proxy()
                            self.proxy = {'http': 'http://' + proxy}
                            print(self.proxy)
                            return self.ajax_post(param_item)
                    print(res.status_code)
                    if res.status_code == '404':
                        proxy = self.get_proxy()
                        self.proxy = {'http': 'http://' + proxy}
                        print(self.proxy)
                        return self.ajax_post(param_item)

        except TypeError as e:
            print(e.args)
            return self.ajax_post(param_item, count + 1)
        except ConnectionError as e:
            print(e.args)
            return self.ajax_post(param_item, count + 1)
        except Exception:
            proxy = self.get_proxy()
            self.proxy = {'http': 'http://' + proxy}
            print(self.proxy)
            return self.ajax_post(param_item)


    def insert_mongo(self,item):
        if self.db['ctrip_comment'].insert(dict(item)):
            print('save to mongo ', item['User_name'])
        else:
            print('No to mongo',item['User_name'])

    def run(self):
        with open('/home/parrot/PycharmProjects/all/ctrip.txt','r') as file:
            for url in file.readlines():
                param_dict = self.get_Param(url.strip('\n'))
                if param_dict:
                    self.ajax_post(param_dict)
                else:
                    continue

if __name__ == '__main__':
    C = Ctrip()
    C.run()
