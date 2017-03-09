#-*-coding:utf-8 -*-
import scrapy
import scrapy_splash
import re
import sys
import time
reload(sys)
sys.setdefaultencoding('utf8')


class ProxySpider(scrapy.Spider):
    name = 'proxy'
    
    
    def start_requests(self):
        self.reqidx = 1
        yield scrapy_splash.SplashRequest(url='http://www.kuaidaili.com/proxylist/1/',method='GET',callback=self.parse)
        
    def parse(self, response):
        source = response.body
        # 将正则表达式编译成Pattern对象 
        pattern = re.compile(r'((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)).+?(\d+)') 
         
        # 使用search()查找匹配的子串，不存在能匹配的子串时将返回None 
        # 这个例子中使用match()无法成功匹配 
        proxys = [];
        for match in re.finditer(pattern,source):
            proxys.append('%s:%s'%(match.group(1),match.group(2)))

        with open('proxys.txt','w') as proxy_file:
            proxy_file.write(','.join(proxys))
        time.sleep(3*60)
        self.reqidx = self.reqidx+1
        yield scrapy_splash.SplashRequest(url='http://www.kuaidaili.com/proxylist/1/#'+str(self.reqidx),method='GET',callback=self.parse)