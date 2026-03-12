import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/oceanengine.db')
conn.row_factory = sqlite3.Row

# 获取最近的fetch_time
cursor = conn.execute('SELECT MAX(fetch_time) as latest_fetch FROM accounts')
latest_fetch = cursor.fetchone()['latest_fetch']

print(f'最近数据时间: {latest_fetch}')
print('='*80)

# 查询最近的账户数据（消耗最高的前20个）
print('\n【账户数据 - 消耗最高的20个】')
rows = conn.execute('''
    SELECT account_name, org_name, cost, daily_roi, daily_pay_amount, account_status
    FROM accounts 
    WHERE fetch_time = ?
    ORDER BY cost DESC 
    LIMIT 20
''', (latest_fetch,)).fetchall()

for i, r in enumerate(rows, 1):
    roi_str = f"{r['daily_roi']:.2f}" if r['daily_roi'] else 'N/A'
    print(f"{i}. {r['account_name']} | 组织: {r['org_name']} | 消耗: {r['cost']:.2f} | ROI: {roi_str} | 状态: {r['account_status']}")

# 查询项目数据（消耗最高的前15个）
print('\n【项目数据 - 消耗最高的15个】')
rows = conn.execute('''
    SELECT project_name, org_name, cost, daily_roi, status
    FROM projects 
    WHERE fetch_time = ?
    ORDER BY cost DESC 
    LIMIT 15
''', (latest_fetch,)).fetchall()

for i, r in enumerate(rows, 1):
    roi_str = f"{r['daily_roi']:.2f}" if r['daily_roi'] else 'N/A'
    print(f"{i}. {r['project_name']} | 组织: {r['org_name']} | 消耗: {r['cost']:.2f} | ROI: {roi_str} | 状态: {r['status']}")

# 统计汇总
print('\n【数据汇总】')
cursor = conn.execute('SELECT COUNT(*) as total, SUM(cost) as total_cost, AVG(daily_roi) as avg_roi FROM accounts WHERE fetch_time = ?', (latest_fetch,))
result = cursor.fetchone()

total_accounts = result['total']
total_cost = result['total_cost'] if result['total_cost'] else 0.0
avg_roi = result['avg_roi']

roi_display = f"{avg_roi:.4f}" if avg_roi is not None else 'N/A'

print(f"账户总数: {total_accounts} | 总消耗: {total_cost:.2f} | 平均ROI: {roi_display}")

cursor = conn.execute('SELECT COUNT(*) as total, SUM(cost) as total_cost FROM projects WHERE fetch_time = ?', (latest_fetch,))
result = cursor.fetchone()

total_projects = result['total']
total_project_cost = result['total_cost'] if result['total_cost'] else 0.0

print(f"项目总数: {total_projects} | 总消耗: {total_project_cost:.2f}")

# 检查是否有需要关注的账户（根据MEMORY.md中的规则）
print('\n【需要关注的账户】')
print('根据监控规则：')
print('- 消耗 ≥ 2000元 且 ROI < 0.09：关注 + 提醒限额到4000')
print('- 已限额账户：消耗占比 ≥ 80% 且 ROI 符合下一放量额度 → 重点提醒')

# 统计符合条件的账户
cursor = conn.execute('''
    SELECT account_name, cost, daily_roi, account_status
    FROM accounts 
    WHERE fetch_time = ?
    AND (cost >= 2000 OR (account_status LIKE '%限额%' AND cost > 0))
    ORDER BY cost DESC
''', (latest_fetch,)).fetchall()

if cursor.rowcount > 0:
    for r in cursor:
        cost = r['cost']
        roi = r['daily_roi']
        status = r['account_status']
        
        alerts = []
        if cost >= 2000:
            if roi and roi < 0.09:
                alerts.append(f"消耗超2000元({cost:.2f})且ROI低于0.09({roi:.2f})，需关注并提醒限额到4000")
            else:
                alerts.append(f"消耗超2000元({cost:.2f})，ROI为{roi:.2f}")
        elif '限额' in status:
            alerts.append(f"账户已限额({status})，当前消耗{cost:.2f}")
        
        for alert in alerts:
            print(f"⚠️ {r['account_name']}: {alert}")
else:
    print('✅ 暂无需要特别关注的账户')

conn.close()
