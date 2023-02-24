#!/usr/bin/python3

import pymysql
import time
import sys

db = pymysql.connect(host='127.0.0.1', port=3306,
                     user='test',password='123456', database='test',
                     cursorclass=pymysql.cursors.SSDictCursor)

# 使用 cursor() 方法创建一个游标对象 cursor
cursor = db.cursor()

# 使用 execute()  方法执行 SQL 查询
cursor.execute("SELECT * FROM tp")

# 使用 fetchone() 方法获取单条数据.
data = cursor.fetchone()

atime = 0
while data:
    print (data)
    sys.stdout.flush()
    if atime < 100:
        time.sleep(30)
        atime = atime + 1
    data = cursor.fetchone()

# 关闭数据库连接
db.close()
