# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('C:\\liangz77\\python_projects\\github_projects\\oceanengine_fetch\\data\\oceanengine.db')
conn.row_factory = sqlite3.Row

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

# 查询昨天所有账户的抓取时间分布
print(f'查询日期: {yesterday}')
print('='*80)

# 查询所有不同的抓取时间点
time_query = '''
SELECT DISTINCT fetch_time
FROM accounts
WHERE date(fetch_time) = ?
ORDER BY fetch_time
'''
time_rows = conn.execute(time_query, (yesterday,)).fetchall()

print(f'昨日所有抓取时间点 (共{len(time_rows)}个):')
for t in time_rows:
    print(f'  {t[0]}')

print()
print('='*80)

# 查询每小时的抓取次数
hour_query = '''
SELECT substr(fetch_time, 12, 2) as hour, COUNT(*) as cnt
FROM accounts
WHERE date(fetch_time) = ?
GROUP BY hour
ORDER BY hour
'''
hour_rows = conn.execute(hour_query, (yesterday,)).fetchall()
print('每小时抓取次数:')
for h in hour_rows:
    bar = '█' * (h[1] // 10)
    print(f'  {h[0]}:00 - {h[0]}:59 : {h[1]:>4}次 {bar}')

# 查询丝话、咕友、缘话的抓取次数
product_query = '''
SELECT
    CASE
        WHEN app_name LIKE '%丝话%' OR account_name LIKE '%丝话%' THEN '丝话'
        WHEN app_name LIKE '%咕友%' OR account_name LIKE '%咕友%' THEN '咕友'
        WHEN app_name LIKE '%缘话%' OR account_name LIKE '%缘话%' THEN '缘话'
        ELSE '其他'
    END as product,
    COUNT(DISTINCT fetch_time) as fetch_times,
    COUNT(DISTINCT account_id) as account_count
FROM accounts
WHERE date(fetch_time) = ?
GROUP BY product
'''
print()
print('='*80)
print('各产品抓取次数:')
product_rows = conn.execute(product_query, (yesterday,)).fetchall()
for p in product_rows:
    print(f'  {p[0]}: {p[1]}个时间点, {p[2]}个账户')

conn.close()