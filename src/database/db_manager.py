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

    def close(self):
        self.conn.close()
