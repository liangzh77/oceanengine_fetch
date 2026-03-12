import sqlite3

conn = sqlite3.connect('data/oceanengine.db')

# Get latest fetch_time
cur = conn.execute("SELECT MAX(fetch_time) as t FROM accounts")
latest = cur.fetchone()[0]
print(f"Latest fetch time: {latest}")

# Account stats by cost desc
print("\n=== Top 10 Accounts by Cost ===")
cur = conn.execute("""
    SELECT account_name, org_name, cost, daily_roi, account_status, account_budget
    FROM accounts WHERE fetch_time = ? ORDER BY cost DESC LIMIT 10
""", (latest,))
for i, r in enumerate(cur.fetchall(), 1):
    roi = r[3] if r[3] else 0
    print(f"{i}. {r[0][:40]} | Cost: {r[2]:.2f} | ROI: {roi:.2f} | Budget: {r[5]} | Status: {r[4]}")

# Projects stats
print("\n=== Top 10 Projects by Cost ===")
cur = conn.execute("""
    SELECT project_name, org_name, cost, daily_roi, status
    FROM projects WHERE fetch_time = ? ORDER BY cost DESC LIMIT 10
""", (latest,))
for i, r in enumerate(cur.fetchall(), 1):
    roi_val = r[3] if r[3] else 0
    print(f"{i}. {r[0][:40]} | Cost: {r[2]:.2f} | ROI: {roi_val:.2f} | Status: {r[4]}")

# Summary
print("\n=== Summary ===")
cur = conn.execute("SELECT COUNT(*), SUM(cost), AVG(daily_roi) FROM accounts WHERE fetch_time = ?", (latest,))
r = cur.fetchone()
roi_avg = r[2] if r[2] else 0
print(f"Accounts: {r[0]} | Total Cost: {r[1]:.2f} | Avg ROI: {roi_avg:.4f}")

cur = conn.execute("SELECT COUNT(*), SUM(cost) FROM projects WHERE fetch_time = ?", (latest,))
r = cur.fetchone()
print(f"Projects: {r[0]} | Total Cost: {r[1]:.2f}")

# Check alerts
print("\n=== Alerts (cost >= 2000 and ROI < 0.09) ===")
cur = conn.execute("""
    SELECT account_name, cost, daily_roi, account_status
    FROM accounts 
    WHERE fetch_time = ? AND cost >= 2000 AND (daily_roi < 0.09 OR daily_roi IS NULL)
""", (latest,))
alerts = cur.fetchall()
if alerts:
    for r in alerts:
        print(f"ALERT: {r[0][:40]} | Cost: {r[1]:.2f} | ROI: {r[2] if r[2] else 'N/A'}")
else:
    print("No alerts - no accounts with cost >= 2000 and low ROI")

conn.close()
