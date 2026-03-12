# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('C:\\liangz77\\python_projects\\github_projects\\oceanengine_fetch\\data\\oceanengine.db')
conn.row_factory = sqlite3.Row

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

# 查询昨天丝话、咕友、缘话账户的抓取时间分布
query = '''
SELECT
    app_name,
    account_name,
    account_id,
    MIN(fetch_time) as first_fetch,
    MAX(fetch_time) as last_fetch,
    COUNT(*) as fetch_count,
    MAX(cost) as max_cost,
    MAX(daily_pay_amount) as max_pay
FROM accounts
WHERE date(fetch_time) = ?
    AND (app_name LIKE '%丝话%' OR app_name LIKE '%咕友%' OR app_name LIKE '%缘话%'
         OR account_name LIKE '%丝话%' OR account_name LIKE '%咕友%' OR account_name LIKE '%缘话%')
GROUP BY account_id
ORDER BY app_name, fetch_count DESC
'''

rows = conn.execute(query, (yesterday,)).fetchall()

print(f'查询日期: {yesterday}')
print('='*120)
print(f'{"产品":<8} {"账户名":<35} {"首次抓取":<20} {"末次抓取":<20} {"抓取次数":>8} {"消耗":>12}')
print('='*120)

for r in rows:
    app = r['app_name'][:6] if r['app_name'] else '-'
    acc = (r['account_name'] or '-')[:32]
    first = r['first_fetch'][11:19] if r['first_fetch'] else '-'
    last = r['last_fetch'][11:19] if r['last_fetch'] else '-'
    count = r['fetch_count']
    cost = r['max_cost'] or 0

# 汇总信息
print()
print('抓取时间分布统计:')

# 查询昨天所有抓取的时间点
time_query = '''
SELECT DISTINCT substr(fetch_time, 12, 5) as hour_min
FROM accounts
WHERE date(fetch_time) = ?
ORDER BY hour_min
'''
time_rows = conn.execute(time_query, (yesterday,)).fetchall()
print(f'昨日抓取时间点: {", ".join([t[0] for t in time_rows])}')

# 查询每小时的抓取次数
hour_query = '''
SELECT substr(fetch_time, 12, 2) as hour, COUNT(*) as cnt
FROM accounts
WHERE date(fetch_time) = ?
GROUP BY hour
ORDER BY hour
'''
hour_rows = conn.execute(hour_query, (yesterday,)).fetchall()
print()
print('每小时抓取次数:')
for h in hour_rows:
    print(f'  {h[0]}:00 - {h[0]}:59 : {h[1]}次')

conn.close()