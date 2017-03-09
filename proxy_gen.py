#-*-coding:utf-8 -*-
import re

source = """
119.84.187.118	8998	高匿名	HTTP, HTTPS	GET, POST	中国 重庆市 重庆市 电信	0.4秒	2分钟前
182.44.149.30	9000	透明	HTTP, HTTPS	GET, POST	中国 山东省 东营市 电信	3秒	1分钟前
117.90.5.219	9000	高匿名	HTTP	GET, POST	中国 江苏省 镇江市 电信	2秒	4分钟前
121.232.145.116	9000	高匿名	HTTP	GET, POST	中国 江苏省 镇江市 电信	0.6秒	7分钟前
121.232.144.178	9000	高匿名	HTTP	GET, POST	中国 江苏省 镇江市 电信	2秒	10分钟前
111.13.7.42	82	高匿名	HTTP	GET, POST	中国 北京市 北京市 移动	3秒	13分钟前
117.90.5.93	9000	高匿名	HTTP	GET, POST	中国 江苏省 镇江市 电信	3秒	16分钟前
218.28.176.246	8080	透明	HTTP, HTTPS	GET, POST	中国 河南省 郑州市 联通	1秒	19分钟前
59.110.154.57	80	匿名	HTTP	GET, POST	中国 北京市 北京市 阿里云	2秒	22分钟前
106.3.240.209	8080	透明	HTTP, HTTP
"""

# 将正则表达式编译成Pattern对象 
pattern = re.compile(r'((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))\s+(\d+)') 
 
# 使用search()查找匹配的子串，不存在能匹配的子串时将返回None 
# 这个例子中使用match()无法成功匹配 
proxys = [];
for match in re.finditer(pattern,source):
    proxys.append('%s:%s'%(match.group(1),match.group(2)))

with open('proxys.txt','w') as proxy_file:
    proxy_file.write(','.join(proxys))

