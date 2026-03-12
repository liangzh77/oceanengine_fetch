# -*- coding: utf-8 -*-
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('C:\\liangz77\\python_projects\\github_projects\\oceanengine_fetch\\data\\oceanengine.db')
conn.row_factory = sqlite3.Row

# 获取今天的日期
today = datetime.now().strftime('%Y-%m-%d')

# 查询丝话相关的账户最新数据
query = '''
SELECT 
    org_name,
    app_name,
    account_name,
    account_id,
    cost,
    daily_roi,
    daily_pay_amount
FROM accounts 
WHERE date(fetch_time) = ?
    AND (app_name LIKE '%丝话%' OR account_name LIKE '%丝话%')
GROUP BY account_id
ORDER BY cost DESC
'''

rows = conn.execute(query, (today,)).fetchall()

# 整理数据
accounts = []
total_cost = 0
total_pay = 0

for r in rows:
    cost = r['cost'] or 0
    pay = r['daily_pay_amount'] or 0
    roi = r['daily_roi'] or 0
    total_cost += cost
    total_pay += pay
    
    accounts.append({
        'org': r['org_name'] or '-',
        'app': r['app_name'] or '-',
        'account': r['account_name'] or '-',
        'account_id': r['account_id'],
        'cost': cost,
        'roi': roi,
        'pay': pay
    })

overall_roi = total_pay / total_cost if total_cost else 0

# 输出JSON格式结果
result = {
    'date': today,
    'summary': {
        'total_cost': round(total_cost, 2),
        'total_pay': round(total_pay, 2),
        'overall_roi': round(overall_roi, 4),
        'account_count': len(accounts)
    },
    'accounts': accounts
}

print(json.dumps(result, ensure_ascii=False, indent=2))
conn.close()