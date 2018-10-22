#!/usr/bin/python3
# coding: utf-8
# Author: EMo

import requests
import sys
import os
import re
import csv
from io import open
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import time,datetime
from functools import wraps
import socket
import threading
import threadpool
from pyquery import PyQuery as pq
from bs4 import BeautifulSoup


""" 时间戳 """
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

""" 获取脚本位置路径 """
path = os.path.split(os.path.realpath(__file__))[0] + '/'
os.chdir(path)

""" Python版本识别 """
if sys.version > '3':
    PY3 = True
    import http.client
else:
    PY3 = False

""" 禁掉Https证书告警输出 """
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

""" 建立线程间公共变量，和线程锁 """
datas = list()
global_locker=threading.Lock()

""" 网页的类 """
class website():
    
    """ 重连列表 """
    reconnectList = list()

    """ 设置类中的重连次数和最大重定向次数 """
    RETRY_TIMES = 0
    MAX_REDIRECTS = 4
    
    """ 请求头 """
    Headers = {
        "Upgrade-Insecure-Requests":'1',
        "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0",
        "Connection": "keep-alive"
    }
    
    Mobil_Headers = {
        "Upgrade-Insecure-Requests":'1',
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
        "Connection": "keep-alive"
    }

    def __init__(self,url,retry=RETRY_TIMES):
        
        # print(url)
        self.retry = retry
        self.url = url
        self.session = requests.Session()
        """ 设置最大重定向次数 """
        self.session.max_redirects = website.MAX_REDIRECTS

        # """ 用于获取IP """
        # self.session.stream = True

        """ 连接失败时重新连接 """
        try:
            self.res = self.session.get(self.url,verify=False,headers=self.Headers,timeout=5)

            print("实际URL为:{}".format(self.res.url))
            
            """ 获取访问时的IP地址不适用于HTTPS """
            # self.ip = self.res.raw._connection.sock.getpeername()[0]
            # if self.url[:5] == "https":
            #     self.ip = self.res.raw._fp.fp.raw
            #     # .ssl_sock.getpeername()[0]
            # else:
            #     self.ip = self.res.raw._fp.fp.raw._sock.getpeername()[0]
           
            """ 解析网页返回内容,解决编码问题 """
            # self.encode = self.res.encoding
            self.encode = self.res.apparent_encoding
            # print(self.encode)
            # print(self.res.encoding)
            if len(self.res.content):
                # self.content = self.res.text  # 不适用于中文
                self.hascontent = True #代替hasattr()函数
                if self.encode:   #自解码
                    try:
                        # print("网页编码为{}".format(self.encode))
                        self.content = self.res.content.decode(self.encode,'ignore')
                    except UnicodeDecodeError:
                        # print(self.res.content)
                        self.content = self.res.content.decode(self.res.encoding,'ignore')
                else:
                    self.content = self.res.content
                
                """ 去除JS和CSS代码 """
                # print(self.content) 
                self.content = filter_tags(self.content)
                # print(self.content)
                      
                """ 生成第三方库格式化后页面对象,供相关函数使用（减少代码重复，并针对处理三方库接受参数的异常）"""
                # pyquery
                try:
                    self.pq_content = pq(self.content)
                except ValueError:
                    self.pq_content = pq(self.res.content)
                # bs4
                self.bs_content = BeautifulSoup(self.content,'lxml')
            else:
                self.hascontent = False
                
        # except ConnectionError as CE: # (DNS faile, refused connection)
        except requests.exceptions.TooManyRedirects as EXC:
            print("{}访问失败,网站跳转过多".format(self.url))
            with open("FailedList.log","a") as f:
                if PY3:
                    f.write("{} {}\n".format(self.url,EXC))
                else:
                    f.write("{} {}\n".format(self.url,EXC).decode("utf-8"))
            # raise
        except Exception as EXC:
            print(EXC)
            if self.retry:
                website(url,self.retry-1)
            else:
                website.addReconnectList(self,url)
                """ 将请求异常和结果存入错误日志中 """
                print("{}访问异常".format(self.url))
                self.hascontent = False
                with open("FailedList.log","a") as f:
                    if PY3:
                        f.write("{} {}\n".format(self.url,EXC))
                    else:
                        f.write("{} {}\n".format(self.url,EXC).decode("utf-8"))
            # raise
    def get_text(self):
        print("正则获取页面中的中文")
        if self.hascontent:
            pattern = re.compile('[\u4e00-\u9fa5]+')
            text = pattern.findall(self.content)
            dedup_text = set()
            for i in text:
                dedup_text.add(i)
            if len(dedup_text):
                print(dedup_text)
                return dedup_text
    
    def get_content(self):
        if self.hascontent:
            return self.content
            # pattern = re.compile('<[^>]*>')
            # pattern = re.compile('</?\w+[^>]*>')
            # content = pattern.sub('',self.content)
            # print(content)
            # return content
    
    def bs_get_text(self):
        if self.hascontent:
            pass


    def pq_get_link(self):
        print("pq获取页面链接")
        if self.hascontent:
            for i in self.pq_content('a').items():
                print(i.attr("href"))
            return self.pq_content('a').items()

    def xp_get_red(self):
        from lxml import etree
        print("xpath获取跳转链接")
        if self.hascontent:
            dom = etree.HTML(self.res.content)
            print(etree.tostring(dom))
            # url = dom.xpath('//meta[@http-equiv="refresh" and @content]/@content')
            # url = dom.xpath('//@window.location.href')
            url = dom.xpath('//@language')[0].text
            print(url)

    def pq_get_text(self):
        print("pq获取页面内容")
        if self.hascontent:
            print(self.pq_content.text())
            return self.pq_content.text()
        #  if self.hascontent:
        #     try:
        #         self.pq_content = pq(self.content)
        #     except ValueError:
        #         self.pq_content = pq(self.res.content)
        #     finally:
        #         return self.pq_content.text()
            

    def pq_get_title(self):
        print("pq获取页面标题")
        if self.hascontent:
            print(self.pq_content('title'))
            return self.pq_content('title')

    def bs_get_title(self):
        print("bs获取页面标题")
        if self.hascontent:
            print(self.bs_content.title)
            return self.bs_content.title
    
    # def soup(self):
    #     # print(self.bs_content.find_all('link'))
    #     # for i in self.bs_content.find_all('a'):
    #     #     # print(i)
    #     #     print(i.get('href'))
    #     # print(self.bs_content.find_all('script'))
    
    
    @staticmethod
    def addReconnectList(self,url):
        """ 添加类中的静态重连列表 """
        website.reconnectList.append(url)

def filter_tags(htmlstr):
    """ 过滤html某些标签 """
    re_script = re.compile('<script.*?</script>', re.S)  # Script
    re_style = re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I)  # style

    s = re_script.sub('', htmlstr)  # 去掉SCRIPT
    s = re_style.sub('', s)  # 去掉style
    """ 去掉多余的空行 """
    blank_line = re.compile('\n+')
    s = blank_line.sub('\n', s)
    return s

def timethis(func):
    '''
    Decorator that reports the execution time.
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = datetime.datetime.now()
        result = func(*args, **kwargs)
        end = datetime.datetime.now()
        print(func.__name__, end-start)
        return result
    return wrapper

def get_url(host):
    """ 判别是否是https """
    conn = http.client.HTTPConnection(host,timeout=5)
    
    try:
        conn.request("HEAD",'')
    except Exception as TE:
        return host,TE
    try:
        if conn.getresponse():
            return "http://"+host
        else:
            return "https://"+host
    except:
        return "https://"+host


def inspect_coinhive(domain):
    global datas
    """ 实现页面检查并将结果，以字典返回 """
    try:
        ip = socket.gethostbyname(domain)
        r = get_url(domain)
        if not len(r) == 2:
            p = website(r,0)
            if hasattr(p,"res"):
                # print("初始化成功！")
                ret = dict(Target=domain,IP=ip,Url=p.res.url,coinhive=p.checkjs())
            else:
                # print(r+"无法访问")
                ret = dict(Target=domain,IP=ip,Url=None,coinhive=None)
        else:
            print(r)
            ret = dict(Target=domain,IP=ip,Url=None,coinhive=None)
    except Exception as e:
        ret = dict(Target=domain,IP=None,Url=None,coinhive=None)
    finally:
        datas.append(ret)
    return ret

@timethis
def main():
    global datas
    if not sys.argv[1][-4:] == "list":
        for url in sys.argv[1:]:
            p = website(url)
            # p.get_text()
            # p.get_content()
            # p.bs_get_text()
            # p.bs_get_title()
            # p.pq_get_title()
            # p.pq_get_link()
            # p.pq_get_text()
            p.xp_get_red()
    else:
        # print("Please Assign Least One URL!")
        with open("result.csv","w") as f:
            dw = csv.DictWriter(f,["Target","Url","Title","Content"])
            dw.writeheader()
            try:
                """ 单线程 """
                for i in open(sys.argv[1],"r"):
                    i = i.strip('\n')
                    # print(i)
                    p = website(i,0)
                    if hasattr(p,"res"):
                        print("初始化成功！")
                        datas.append(dict(Target=p.url,Url=p.res.url,Title=p.pq_get_title(),Content=p.get_content()))
                    else:
                        print("无法访问")
                        datas.append(dict(Target=p.url,Url=None,Title=None,Content=None))
            #     """ 多线程 """
            #     with open(sys.argv[1],"r") as f:
            #         argslist = f.read().splitlines()
            #         threadRequests = threadpool.makeRequests(website,argslist)
            #         for request in threadRequests:
            #             thdpol.putRequest(request)
            #         thdpol.wait()
            finally:
                dw.writerows(datas)
                print(website.reconnectList)

if __name__ == '__main__':
    main()
