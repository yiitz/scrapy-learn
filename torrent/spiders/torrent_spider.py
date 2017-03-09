#-*-coding:utf-8 -*-
import scrapy
import scrapy_splash
import json
import urllib2
import sys
import time
import logging
import logging.config
import hashlib
import MySQLdb
import traceback

reload(sys)
sys.setdefaultencoding('utf8')


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s [%(name)s:%(lineno)d] [%(levelname)s]- %(message)s'
        },
        'standard': {
            'format': '%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] [%(levelname)s]- %(message)s'
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },

        'default': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'filename': 'torrent%s.log'%(time.strftime('%Y-%m-%d_%H_%M_%S')),
            'mode': 'w+',
            'maxBytes': 1024*1024,  # 1 MB
            'backupCount': 20,
            'encoding': 'utf-8'
        },
    },
    'root': {
        'handlers': ['default','console'],
        'level': 'INFO',
        'propagate': False
    }
}

logging.config.dictConfig(LOGGING)


class TorrentSpider(scrapy.Spider):
    name = 'torrent'
    es_url='http://localhost:9200/resource/torrent/_bulk'

    failed_log = open("failed.txt", "a")

    proxy_dict = {}
    proxy_dict_last_update = 1

    @classmethod
    def load_proxy_dict(cls):
        cls.proxy_dict = {}
        with open('proxys.txt','r') as proxy_file:
            for p in proxy_file.read().split(','):
                if len(p) > 5:
                    cls.proxy_dict[p] = 1
        cls.proxy_dict_last_update = time.time()

    @classmethod
    def sort_prixy_dict(cls):
        return sorted(cls.proxy_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)

    def __init__(self, category=None, *args, **kwargs):
        super(TorrentSpider, self).__init__(*args, **kwargs)
        self.params = []
        self.connect_db()
        self.fetch_count=0
        
    def connect_db(self):
        try:
            self.db = MySQLdb.connect('localhost','root','000000','scrapy')
            self.db.ping(True)
            self.db.set_character_set('utf8')
            self.cursor = self.db.cursor()
            self.cursor.execute('SET NAMES utf8;')
            self.cursor.execute('SET CHARACTER SET utf8;')
            self.cursor.execute('SET character_set_connection=utf8;')
        except BaseException as error:
            self.logger.error('connect db error:')
            self.logger.error(error)
        
    def close_db(self):
        try:
            self.cursor.close()
            self.db.close()
        except BaseException as error:
            self.logger.error('close db error:')
            self.logger.error(error)

    def start_requests(self):
        self.logger.info('TorrentSpider begin.')
        if (time.time()-TorrentSpider.proxy_dict_last_update) > 3*60: TorrentSpider.load_proxy_dict()
        script = None
        with open ("torrent_lua.lua", "r") as script_file:
            script = script_file.read()
        # urls = []
        # for url in urls:
            # yield scrapy_splash.SplashRequest(url=url,
            # method='GET', 
            # callback=self.parse,
            # endpoint='execute',
            # dont_filter=True,
            # meta={'splash':{'download_timeout' :300,'timeout':300}},
            # args={'lua_source': script,'proxys':[x for x,y in TorrentSpider.sort_prixy_dict()]})

        self.execute_sql('select * from keywords where del=0 limit 1')
        kw = self.cursor.fetchone()
        if kw:
            yield scrapy_splash.SplashRequest(url='http://btkitty.bid/',dont_filter=True,
            method='POST', 
            body=json.dumps({'keyword':kw[0],'hidden':'true'}),
            callback=self.parse,
            endpoint='execute',
            headers={'Referer':'http://btkitty.bid/'},
            args={'lua_source': script,'proxys':[x for x,y in TorrentSpider.sort_prixy_dict()]})
            self.execute_sql('update keywords set del=1 where `keyword`=%s',(kw[0],))
            #kw = self.cursor.fetchone()
        else:
            self.execute_sql('select * from crawl_queue limit 100')
            cq = self.cursor.fetchone()
            while cq:
                yield scrapy_splash.SplashRequest(url=cq[1],
                method='GET', 
                callback=self.parse,
                endpoint='execute',
                headers={'Referer':cq[2]},
                args={'lua_source': script,'proxys':[x for x,y in TorrentSpider.sort_prixy_dict()]})
                self.execute_sql('delete from crawl_queue where `id`=%d',(cq[0],))
                cq = self.cursor.fetchone()

    def parse(self, response):

        if response.data.has_key('p'):
            p = response.data['p']
            for x,y in sort_prixy_dict():
                if p == x:
                    break
                TorrentSpider.proxy_dict[x] = TorrentSpider.proxy_dict[x]-1
            TorrentSpider.proxy_dict[p] = TorrentSpider.proxy_dict[p]+1
            

        if (time.time()-TorrentSpider.proxy_dict_last_update) > 3*60: TorrentSpider.load_proxy_dict()
        
        script = None
        with open ('torrent_lua.lua', 'r') as script_file:
            script = script_file.read()
            
        if self.fetch_count == 50:
            self.fetch_count = 0

        depth=response.meta['depth']
        is_torrent=response.url.startswith('http://btkitty.bid/torrent/')
        for url in response.css('a[href^="http://btkitty.bid/search/"]::attr(href),a[href^="http://btkitty.bid/torrent/"]::attr(href)').extract():
            priority = depth+1
            dont_filter = False
            
            if url.startswith('http://btkitty.bid/torrent/'):
                priority = 10
            if (not is_torrent) and (depth < 4):
                yield scrapy_splash.SplashRequest(url=url, callback=self.parse,endpoint='execute',dont_filter=dont_filter,
                #cache_args=['lua_source'],
                headers={'Referer':response.url},
                priority=priority,
                args={'lua_source': script,'proxys':[x for x,y in TorrentSpider.sort_prixy_dict()],'clearcookie':self.fetch_count == 0})
            else:
                self.execute_sql('insert into crawl_queue (url,refer) values(%s,%s)',(url,response.url,))
        self.fetch_count = self.fetch_count + 1

        if is_torrent:
            magnet = response.css('a[href^="magnet"]::attr(href)').extract()
            torrent = response.css('dd:contains(".torrent")::text').extract()
            files = response.css('span.filename::text').extract()
            infohash = response.css('dd.infohash::text').extract()
            if len(magnet) > 0 and len(torrent) > 0:
                self.execute_sql('replace into torrent values(%s,%s)',(infohash[0] if len(infohash) > 0 else hashlib.md5(magnet[0]).hexdigest(),'{"magnet":"%s","torrentName":"%s","files":%s,"orginUrl":"%s"}'%(magnet[0],torrent[0],json.dumps(files) if files else 'null',response.url)))
                # self.params.append('{ "index": {"_id":"%s"}}'%(infohash[0] if len(infohash) > 0 else hashlib.md5(magnet[0]).hexdigest()))
                # self.params.append('{"magnet":"%s","torrentName":"%s","files":%s,"orginUrl":"%s"}'%(magnet[0],torrent[0],json.dumps(files) if files else 'null',response.url))

            # if len(self.params) == 10:
                # self.index_torrents()
                
                
    def execute_sql(self,sql,params=None):
        for i in range(3):
            try:
               # 执行sql语句
               self.cursor.execute(sql,params)
               # 提交到数据库执行
               self.db.commit()
               return
            except BaseException as error:
                self.logger.error('execute sql error:')
                self.logger.error(error)
                traceback.print_stack()
               # Rollback in case there is any error
                self.close_db()
                time.sleep(3)
                self.connect_db()
        TorrentSpider.failed_log.write('%s,%s\n'%(sql,repr(params)))
        TorrentSpider.failed_log.flush()

    def index_torrents(self):
        ok = False
        for i in range(3):
            if self.bulk_insert():
                ok = True
                break
            time.sleep(2)
        if not ok:
            body = '\n'.join(self.params) + '\n'
            TorrentSpider.failed_log.write(body)
            TorrentSpider.failed_log.flush()
            self.logger.error(body)
        self.params = []

    def bulk_insert(self):
        try:
            req = urllib2.Request(url=TorrentSpider.es_url)
            req.add_header('Content-type', 'application/json')
            req.get_method = lambda: "PUT"
            req.add_data('\n'.join(self.params) + '\n')
            response = urllib2.urlopen(req)
            data = json.load(response)
            if str(data['errors']) != 'False':
                self.logger.error('bulk_insert error:'+str(data))
                return False
            return True
        except urllib2.HTTPError as e:
            self.logger.error('bulk_insert error:'+str(e.code))
            self.logger.error(e.read())
            return False

    def closed(self, reason):
        self.close_db()
        # if len(self.params) > 0:
            # self.index_torrents()
