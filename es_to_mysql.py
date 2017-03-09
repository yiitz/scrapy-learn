#-*-coding:utf-8 -*-
import MySQLdb

# 打开数据库连接
db = MySQLdb.connect('localhost','root','000000','scrapy')

# 使用cursor()方法获取操作游标 
cursor = db.cursor()

# SQL 插入语句
sql = 'replace into torrent values("%s","%s")'%('a','b')
try:
   # 执行sql语句
   cursor.execute(sql)
   # 提交到数据库执行
   db.commit()
except:
   # Rollback in case there is any error
   db.rollback()

# 关闭数据库连接
db.close()