import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('C:\\liangz77\\python_projects\\github_projects\\oceanengine_fetch\\data\\oceanengine.db')
conn.row_factory = sqlite3.Row

# 获取昨天的日期
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
print(f'查询日期: {yesterday}')
print('='*80)

# 查询昨天的账户数据
query = '''
SELECT 
    org_name,
    app_name,
    account_name,
    account_id,
    account_status,
    MAX(fetch_time) as last_fetch_time,
    cost,
    daily_roi,
    daily_pay_amount,
    impressions,
    clicks,
    conversions
FROM accounts 
WHERE date(fetch_time) = ?
GROUP BY account_id
ORDER BY cost DESC
'''

rows = conn.execute(query, (yesterday,)).fetchall()

if not rows:
    # 如果没有精确匹配，尝试模糊查询
    rows = conn.execute('''
        SELECT DISTINCT date(fetch_time) as dt FROM accounts 
        WHERE date(fetch_time) >= date('now', '-3 days')
        ORDER BY dt DESC
    ''').fetchall()
    print('可用日期:')
    for r in rows:
        print(f'  - {r[0]}')
else:
    # 打印汇总
    total_cost = 0
    total_pay = 0
    for r in rows:
        cost = r['cost'] or 0
        pay = r['daily_pay_amount'] or 0
        total_cost += cost
        total_pay += pay
    
    print(f'\nYesterday Summary ({yesterday})')
    print(f'   Total Cost: RMB {total_cost:,.2f}')
    print(f'   Total Pay: RMB {total_pay:,.2f}')
    print(f'   Overall ROI: {(total_pay/total_cost if total_cost else 0):.4f}')
    print(f'   Account Count: {len(rows)}')
    print()
    
    # Print detailed data
    print('Account Details')
    print('-'*100)
    print(f'{"Org":<10} {"App":<12} {"Account":<20} {"Cost":>10} {"ROI":>8} {"Pay":>10}')
    print('-'*100)
    
    for r in rows:
        org = (r['org_name'] or '-')[:8]
        app = (r['app_name'] or '-')[:10]
        acc = (r['account_name'] or '-')[:18]
        cost = r['cost'] or 0
        roi = r['daily_roi'] or 0
        pay = r['daily_pay_amount'] or 0
        print(f'{org:<10} {app:<12} {acc:<20} {cost:>10.2f} {roi:>8.4f} {pay:>10.2f}')
    
    print('-'*100)

conn.close()