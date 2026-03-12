
import sqlite3
from datetime import datetime
import sys

# 设置输出编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

conn = sqlite3.connect('data/oceanengine.db')
conn.row_factory = sqlite3.Row

# 查最近一轮数据
cursor = conn.execute('SELECT * FROM accounts ORDER BY fetch_time DESC LIMIT 30')
rows = cursor.fetchall()

if not rows:
    print('暂无账户数据')
else:
    # 获取最新的抓取时间
    latest_time = rows[0]['fetch_time']
    print(f'=== 最近抓取时间: {latest_time} ===\n')
    
    # 汇总数据
    total_cost = 0
    total_pay = 0
    account_count = 0
    active_accounts = 0
    
    print(f'{'账户名称':<25} {'消耗':>10} {'ROI':>8} {'付费金额':>12}')
    print('-' * 70)
    
    for r in rows:
        cost = r['cost'] if r['cost'] else 0
        roi = r['daily_roi'] if r['daily_roi'] else 0
        pay = r['daily_pay_amount'] if r['daily_pay_amount'] else 0
        
        if cost > 0:
            active_accounts += 1
            
        total_cost += cost
        total_pay += pay
        account_count += 1
        
        cost_str = f'{cost:,.0f}' if cost > 0 else '-'
        roi_str = f'{roi:.2f}' if roi > 0 else '-'
        pay_str = f'{pay:,.0f}' if pay > 0 else '-'
        
        # 解码账户名称
        account_name = r['account_name']
        if isinstance(account_name, bytes):
            account_name = account_name.decode('utf-8')
        
        print(f'{account_name:<25} {cost_str:>10} {roi_str:>8} {pay_str:>12}')
    
    print('-' * 70)
    overall_roi = total_pay / total_cost if total_cost > 0 else 0
    # 使用f-string格式化总计
    print(f"{'总计 (' + str(account_count) + ' 个账户, ' + str(active_accounts) + ' 个活跃)':<25} {total_cost:>10,.0f} {overall_roi:>8.2f}")
    print(f"{'':<25} {'整体付费金额:':>10} {total_pay:>12,.0f}")

conn.close()
