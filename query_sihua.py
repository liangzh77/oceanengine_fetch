import sqlite3
from datetime import datetime

conn = sqlite3.connect('C:\\liangz77\\python_projects\\github_projects\\oceanengine_fetch\\data\\oceanengine.db')
conn.row_factory = sqlite3.Row

# 获取今天的日期
today = datetime.now().strftime('%Y-%m-%d')
print(f'查询日期: {today}')
print('='*100)

# 查询丝话相关的账户最新数据
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
    AND (app_name LIKE '%丝话%' OR account_name LIKE '%丝话%')
GROUP BY account_id
ORDER BY cost DESC
'''

rows = conn.execute(query, (today,)).fetchall()

if not rows:
    # 尝试查找所有包含丝话的账户，不限日期
    print('今天暂无丝话账户数据，查询所有历史数据中的丝话账户...')
    query_all = '''
    SELECT 
        org_name,
        app_name,
        account_name,
        account_id,
        MAX(fetch_time) as last_fetch_time,
        cost,
        daily_roi,
        daily_pay_amount
    FROM accounts 
    WHERE app_name LIKE '%丝话%' OR account_name LIKE '%丝话%'
    GROUP BY account_id
    ORDER BY last_fetch_time DESC, cost DESC
    LIMIT 20
    '''
    rows = conn.execute(query_all).fetchall()
    
    if rows:
        print(f'\n找到 {len(rows)} 个丝话相关账户（显示最新数据）：')
        print('-'*100)
        print(f'{"组织":<15} {"应用":<12} {"账户":<25} {"时间":<20} {"消耗":>10} {"ROI":>8}')
        print('-'*100)
        
        total_cost = 0
        for r in rows:
            org = (r['org_name'] or '-')[:12]
            app = (r['app_name'] or '-')[:10]
            acc = (r['account_name'] or '-')[:22]
            time_str = r['last_fetch_time'][:16] if r['last_fetch_time'] else '-'
            cost = r['cost'] or 0
            roi = r['daily_roi'] or 0
            total_cost += cost
            print(f'{org:<15} {app:<12} {acc:<25} {time_str:<20} {cost:>10.2f} {roi:>8.4f}')
        
        print('-'*100)
        print(f'合计消耗: RMB {total_cost:,.2f}')
else:
    # 打印今天丝话账户的汇总
    total_cost = 0
    total_pay = 0
    for r in rows:
        cost = r['cost'] or 0
        pay = r['daily_pay_amount'] or 0
        total_cost += cost
        total_pay += pay
    
    print(f'\n丝话账户今日汇总 ({today})')
    print(f'   总消耗: RMB {total_cost:,.2f}')
    print(f'   总付费: RMB {total_pay:,.2f}')
    print(f'   整体ROI: {(total_pay/total_cost if total_cost else 0):.4f}')
    print(f'   账户数: {len(rows)}')
    print()
    
    # 打印详细数据
    print('各账户详情')
    print('-'*100)
    print(f'{"组织":<15} {"应用":<12} {"账户":<25} {"消耗":>10} {"ROI":>8} {"付费":>10}')
    print('-'*100)
    
    for r in rows:
        org = (r['org_name'] or '-')[:12]
        app = (r['app_name'] or '-')[:10]
        acc = (r['account_name'] or '-')[:22]
        cost = r['cost'] or 0
        roi = r['daily_roi'] or 0
        pay = r['daily_pay_amount'] or 0
        print(f'{org:<15} {app:<12} {acc:<25} {cost:>10.2f} {roi:>8.4f} {pay:>10.2f}')
    
    print('-'*100)

conn.close()