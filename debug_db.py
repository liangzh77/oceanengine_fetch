import sqlite3

conn = sqlite3.connect('data/oceanengine.db')

# Get accounts schema
cur = conn.execute("PRAGMA table_info(accounts)")
print("Accounts schema:")
for r in cur.fetchall():
    print(r)

# Get latest data
cur = conn.execute("SELECT * FROM accounts ORDER BY rowid DESC LIMIT 5")
rows = cur.fetchall()

# Get column names
cur = conn.execute("PRAGMA table_info(accounts)")
cols = [r[1] for r in cur.fetchall()]
print("\nColumns:", cols)

print("\nLatest accounts data:")
for r in rows:
    row_dict = dict(zip(cols, r))
    print(row_dict)

# Summary
cur = conn.execute("SELECT COUNT(*) as cnt, SUM(cost) as total_cost FROM accounts")
result = cur.fetchone()
print(f"\nSummary: {result[0]} accounts, total cost: {result[1]}")

conn.close()
