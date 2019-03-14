import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException,StaleElementReferenceException,NoSuchWindowException
from lxml import etree
import pymongo
import requests
import urllib.request

class Mafengwo():

    def __init__(self):
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 10)
        self.browser.set_window_size(1400, 900)
        self.start_url = ''
        self.base_url = 'http://www.mafengwo.cn'
        self.client = pymongo.MongoClient("localhost",27017)
        self.db = self.client["mafengwo"]
        
    def get_html(self,url):
        item = {}
        item["link"] = url
        self.browser.get(item["link"])
        links = self.browser.find_elements_by_xpath("//div[@class='mod mod-reviews']/div[@class='review-nav']/ul/li/a")
        for link in links:
            self.browser.execute_script("arguments[0].click();", link)
            time.sleep(1)
            doc = etree.HTML(self.browser.page_source)
            self.feng(doc)
        return self.browser

    def feng(self,doc):
        # doc = etree.HTML(self.browser.page_source)
        li_list = doc.xpath("//div[@class='_j_commentlist']/div/ul/li")
        for li in li_list:
            item ={}
            title = re.findall(r'<h1>(.*?)</h1>',self.browser.page_source)
            item["title"] = title[0] if len(title) > 0 else None
            user_link = li.xpath("./div[@class='user']/a/@href")
            item["user_link"] = self.base_url + user_link[0] if len(user_link) > 0 else None
            ret = re.compile(r'/u/(.*?).html')
            id = re.findall(ret,item["user_link"])
            item["id"] = id[0] if len(id) > 0 else None
            if id:
                level = li.xpath("./div[@class='user']/span[@class='level']/text()")
                item["level"] = level[0]
                name = li.xpath("./a[@class='name']/text()")
                item["name"] = name[0]
                comment = li.xpath("./p[@class='rev-txt']/text()")
                item["comment"] = ''.join(comment) if len(comment) > 0 else None
                time = li.xpath("./div[@class='info clearfix']/span[@class='time']/text()")
                item["time"] = time[0] if len(time) >0 else None
                print(item)
                self.insert_mongodb(item)
        import time
        time.sleep(1)
        try:
            # self.wait.until(EC.presence_of_element_located((By.XPATH, "//a[@class='pi pg-next']")))
            next_page = self.wait.until(EC.element_to_be_clickable((By.XPATH,"//a[@class='pi pg-next']")))
            if next_page:
                next_page.click()
                import time
                time.sleep(1.5)
                doc_html = etree.HTML(self.browser.page_source)
                return self.feng(doc_html)
            else:
                pass
        except NoSuchWindowException:
            print("No Page ##########")
            pass
        except TimeoutException:
            print("Timeout ##########")
            pass
        except StaleElementReferenceException:
            print("No Page ##########")
            pass

    def insert_mongodb(self,item):
        if self.db['mafengwo_comment'].insert(dict(item)):
            print('save to mongo ', item['name'])
        else:
            print('No to mongo',item['name'])
    def run(self):
        with open('/home/parrot/PycharmProjects/all/mafeng.txt','r') as f:
            for url in f.readlines()[72:]:
                self.get_html(url.strip('\n'))

if __name__ == '__main__':
    M = Mafengwo()
    M.run()
    # M.get_html("http://www.mafengwo.cn/poi/6047483.html")
    # M.feng()
