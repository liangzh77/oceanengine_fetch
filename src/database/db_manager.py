"""数据库管理模块：SQLite 建表、数据写入"""
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS fetch_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    fetch_time TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    account_name TEXT,
    account_budget REAL,
    cost REAL,
    daily_roi REAL,
    raw_data TEXT,
    FOREIGN KEY (batch_id) REFERENCES fetch_batches(id)
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    project_name TEXT,
    project_budget REAL,
    cost REAL,
    daily_roi REAL,
    status TEXT,
    bid_price REAL,
    raw_data TEXT,
    FOREIGN KEY (batch_id) REFERENCES fetch_batches(id)
);

CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    unit_name TEXT,
    cost REAL,
    daily_roi REAL,
    status TEXT,
    raw_data TEXT,
    FOREIGN KEY (batch_id) REFERENCES fetch_batches(id)
);

CREATE INDEX IF NOT EXISTS idx_accounts_batch ON accounts(batch_id);
CREATE INDEX IF NOT EXISTS idx_projects_batch ON projects(batch_id);
CREATE INDEX IF NOT EXISTS idx_units_batch ON units(batch_id);
CREATE INDEX IF NOT EXISTS idx_batches_time ON fetch_batches(fetch_time);
"""


class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()
        logger.info(f"database initialized: {self.db_path}")

    def create_batch(self, org_name: str, app_name: str, fetch_time: datetime = None) -> int:
        if fetch_time is None:
            fetch_time = datetime.now()
        cur = self.conn.execute(
            "INSERT INTO fetch_batches (org_name, app_name, fetch_time) VALUES (?, ?, ?)",
            (org_name, app_name, fetch_time.isoformat()),
        )
        self.conn.commit()
        return cur.lastrowid

    def insert_accounts(self, batch_id: int, rows: list[dict]):
        for r in rows:
            self.conn.execute(
                "INSERT INTO accounts (batch_id, account_name, account_budget, cost, daily_roi, raw_data) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (batch_id, r.get("account_name"), r.get("account_budget"),
                 r.get("cost"), r.get("daily_roi"), r.get("raw_data")),
            )
        self.conn.commit()
        logger.info(f"inserted {len(rows)} accounts for batch {batch_id}")

    def insert_projects(self, batch_id: int, rows: list[dict]):
        for r in rows:
            self.conn.execute(
                "INSERT INTO projects (batch_id, project_name, project_budget, cost, daily_roi, status, bid_price, raw_data) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (batch_id, r.get("project_name"), r.get("project_budget"),
                 r.get("cost"), r.get("daily_roi"), r.get("status"),
                 r.get("bid_price"), r.get("raw_data")),
            )
        self.conn.commit()
        logger.info(f"inserted {len(rows)} projects for batch {batch_id}")

    def insert_units(self, batch_id: int, rows: list[dict]):
        for r in rows:
            self.conn.execute(
                "INSERT INTO units (batch_id, unit_name, cost, daily_roi, status, raw_data) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (batch_id, r.get("unit_name"), r.get("cost"),
                 r.get("daily_roi"), r.get("status"), r.get("raw_data")),
            )
        self.conn.commit()
        logger.info(f"inserted {len(rows)} units for batch {batch_id}")

    def get_latest_data(self) -> dict:
        """获取最新一轮抓取的所有数据，按组织分组"""
        # 找到最新的 fetch_time（同一轮抓取的多个 batch 时间接近）
        row = self.conn.execute(
            "SELECT MAX(fetch_time) FROM fetch_batches"
        ).fetchone()
        if not row or not row[0]:
            return {}

        latest_time = row[0]
        # 取最近5分钟内的所有 batch（同一轮抓取）
        batches = self.conn.execute(
            "SELECT id, org_name, app_name, fetch_time FROM fetch_batches "
            "WHERE fetch_time >= datetime(?, '-5 minutes') ORDER BY id",
            (latest_time,),
        ).fetchall()

        if not batches:
            return {}

        batch_ids = [b[0] for b in batches]
        placeholders = ",".join("?" * len(batch_ids))

        result = {"batches": [], "accounts": [], "projects": [], "units": []}

        for b in batches:
            result["batches"].append({
                "batch_id": b[0], "org_name": b[1],
                "app_name": b[2], "fetch_time": b[3],
            })

        for row in self.conn.execute(
            f"SELECT batch_id, account_name, account_budget, cost, daily_roi "
            f"FROM accounts WHERE batch_id IN ({placeholders})", batch_ids,
        ).fetchall():
            result["accounts"].append({
                "batch_id": row[0], "account_name": row[1],
                "account_budget": row[2], "cost": row[3], "daily_roi": row[4],
            })

        for row in self.conn.execute(
            f"SELECT batch_id, project_name, project_budget, cost, daily_roi, status, bid_price "
            f"FROM projects WHERE batch_id IN ({placeholders})", batch_ids,
        ).fetchall():
            result["projects"].append({
                "batch_id": row[0], "project_name": row[1],
                "project_budget": row[2], "cost": row[3],
                "daily_roi": row[4], "status": row[5], "bid_price": row[6],
            })

        for row in self.conn.execute(
            f"SELECT batch_id, unit_name, cost, daily_roi, status "
            f"FROM units WHERE batch_id IN ({placeholders})", batch_ids,
        ).fetchall():
            result["units"].append({
                "batch_id": row[0], "unit_name": row[1],
                "cost": row[2], "daily_roi": row[3], "status": row[4],
            })

        return result

    def close(self):
        self.conn.close()
