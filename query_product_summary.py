# -*- coding: utf-8 -*-
import sqlite3
import json
from datetime import datetime, timedelta

conn = sqlite3.connect('C:\\liangz77\\python_projects\\github_projects\\oceanengine_fetch\\data\\oceanengine.db')
conn.row_factory = sqlite3.Row

# 获取昨天的日期
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
print(f'查询日期: {yesterday}')

# 查询丝话、咕友、缘话相关账户的昨日数据
query = '''
SELECT 
    org_name,
    app_name,
    account_name,
    account_id,
    cost,
    daily_roi,
    daily_pay_amount,
    impressions,
    clicks,
    conversions
FROM accounts 
WHERE date(fetch_time) = ?
    AND (app_name LIKE '%丝话%' OR app_name LIKE '%咕友%' OR app_name LIKE '%缘话%'
         OR account_name LIKE '%丝话%' OR account_name LIKE '%咕友%' OR account_name LIKE '%缘话%')
GROUP BY account_id
ORDER BY app_name, cost DESC
'''

rows = conn.execute(query, (yesterday,)).fetchall()

# 按产品维度汇总
products = {}
total_cost = 0
total_pay = 0

for r in rows:
    # 提取产品名称
    app_name = r['app_name'] or ''
    account_name = r['account_name'] or ''
    
    # 判断产品类型
    if '丝话' in app_name or '丝话' in account_name:
        product = '丝话'
    elif '咕友' in app_name or '咕友' in account_name:
        product = '咕友'
    elif '缘话' in app_name or '缘话' in account_name:
        product = '缘话'
    else:
        product = app_name[:10] if app_name else '其他'
    
    if product not in products:
        products[product] = {
            'product': product,
            'accounts': [],
            'total_cost': 0,
            'total_pay': 0,
            'total_impressions': 0,
            'total_clicks': 0,
            'total_conversions': 0,
            'account_count': 0
        }
    
    cost = r['cost'] or 0
    pay = r['daily_pay_amount'] or 0
    imp = r['impressions'] or 0
    clicks = r['clicks'] or 0
    conv = r['conversions'] or 0
    
    products[product]['accounts'].append({
        'account_name': account_name,
        'account_id': r['account_id'],
        'cost': cost,
        'roi': r['daily_roi'] or 0,
        'pay': pay,
        'impressions': imp,
        'clicks': clicks,
        'conversions': conv
    })
    
    products[product]['total_cost'] += cost
    products[product]['total_pay'] += pay
    products[product]['total_impressions'] += imp
    products[product]['total_clicks'] += clicks
    products[product]['total_conversions'] += conv
    products[product]['account_count'] += 1
    
    total_cost += cost
    total_pay += pay

# 计算各产品ROI
for product in products:
    p = products[product]
    p['roi'] = p['total_pay'] / p['total_cost'] if p['total_cost'] > 0 else 0

overall_roi = total_pay / total_cost if total_cost > 0 else 0

# 输出结果
result = {
    'date': yesterday,
    'products': list(products.values()),
    'summary': {
        'total_cost': round(total_cost, 2),
        'total_pay': round(total_pay, 2),
        'overall_roi': round(overall_roi, 4)
    }
}

print(json.dumps(result, ensure_ascii=False, indent=2))
conn.close()