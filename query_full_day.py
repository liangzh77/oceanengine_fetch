# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('C:\\liangz77\\python_projects\\github_projects\\oceanengine_fetch\\data\\oceanengine.db')
conn.row_factory = sqlite3.Row

# 查询3月11日的所有数据
# 对于每个账户，取3月11日最新的那条记录（代表当天0-24点的累计消耗）
query = '''
SELECT 
    app_name,
    account_name,
    account_id,
    cost,
    daily_roi,
    daily_pay_amount,
    impressions,
    clicks,
    conversions,
    fetch_time
FROM accounts 
WHERE date(fetch_time) = '2026-03-11'
    AND (app_name LIKE '%丝话%' OR app_name LIKE '%咕友%' OR app_name LIKE '%缘话%'
         OR account_name LIKE '%丝话%' OR account_name LIKE '%咕友%' OR account_name LIKE '%缘话%')
ORDER BY account_id, fetch_time DESC
'''

rows = conn.execute(query).fetchall()

# 对于每个账户，只取最新的一条记录
accounts_data = {}
for r in rows:
    acc_id = r['account_id']
    if acc_id not in accounts_data:
        accounts_data[acc_id] = {
            'app_name': r['app_name'],
            'account_name': r['account_name'],
            'account_id': acc_id,
            'cost': r['cost'],
            'daily_roi': r['daily_roi'],
            'daily_pay_amount': r['daily_pay_amount'],
            'impressions': r['impressions'],
            'clicks': r['clicks'],
            'conversions': r['conversions'],
            'fetch_time': r['fetch_time']
        }

# 按产品维度汇总
products = {}
total_cost = 0
total_pay = 0

for acc_id, r in accounts_data.items():
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
        continue  # 跳过非目标产品

    if product not in products:
        products[product] = {
            'product': product,
            'accounts': [],
            'total_cost': 0,
            'total_pay': 0,
            'account_count': 0
        }

    cost = r['cost'] or 0
    pay = r['daily_pay_amount'] or 0

    products[product]['accounts'].append({
        'account_name': account_name,
        'account_id': r['account_id'],
        'cost': cost,
        'roi': r['daily_roi'] or 0,
        'pay': pay,
        'impressions': r['impressions'] or 0,
        'clicks': r['clicks'] or 0,
        'conversions': r['conversions'] or 0,
        'fetch_time': r['fetch_time']
    })

    products[product]['total_cost'] += cost
    products[product]['total_pay'] += pay
    products[product]['account_count'] += 1

    total_cost += cost
    total_pay += pay

# 计算各产品ROI
for product in products:
    p = products[product]
    p['roi'] = round(p['total_pay'] / p['total_cost'], 4) if p['total_cost'] > 0 else 0

overall_roi = round(total_pay / total_cost, 4) if total_cost > 0 else 0

print(f"2026-03-11 各产品汇总")
print(f"=" * 60)
print(f"总消耗: {total_cost:.2f}")
print(f"总付费: {total_pay:.2f}")
print(f"整体ROI: {overall_roi}")
print()

for product in ['丝话', '咕友', '缘话']:
    if product in products:
        p = products[product]
        print(f"\n【{product}】账户数: {p['account_count']}")
        print(f"  消耗: {p['total_cost']:.2f}, 付费: {p['total_pay']:.2f}, ROI: {p['roi']}")
        # 按消耗排序显示前10个账户
        sorted_accs = sorted(p['accounts'], key=lambda x: x['cost'], reverse=True)
        for i, acc in enumerate(sorted_accs[:10], 1):
            if acc['cost'] > 0:
                print(f"    {i}. {acc['account_name'][:30]}... 消耗:{acc['cost']:.2f} ROI:{acc['roi']}")

conn.close()