"""数据库管理模块：SQLite 时间序列数据模型"""
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    fetch_time TEXT NOT NULL,
    account_count INTEGER DEFAULT 0,
    project_count INTEGER DEFAULT 0,
    unit_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    fetch_time TEXT NOT NULL,
    account_name TEXT,
    account_id TEXT,
    account_status TEXT,
    account_budget REAL,
    cost REAL,
    daily_roi REAL,
    daily_pay_amount REAL,
    impressions REAL,
    clicks REAL,
    conversions REAL,
    avg_conversion_cost REAL
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    fetch_time TEXT NOT NULL,
    project_name TEXT,
    project_id TEXT,
    status TEXT,
    project_budget REAL,
    cost REAL,
    daily_roi REAL,
    impressions REAL,
    conversions REAL,
    avg_conversion_cost REAL
);

CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    fetch_time TEXT NOT NULL,
    unit_name TEXT,
    unit_id TEXT,
    status TEXT,
    cost REAL,
    daily_roi REAL,
    daily_pay_amount REAL,
    impressions REAL,
    clicks REAL,
    conversions REAL,
    avg_conversion_cost REAL
);

CREATE INDEX IF NOT EXISTS idx_accounts_ts ON accounts(account_name, fetch_time);
CREATE INDEX IF NOT EXISTS idx_projects_ts ON projects(project_name, fetch_time);
CREATE INDEX IF NOT EXISTS idx_units_ts ON units(unit_name, fetch_time);
CREATE INDEX IF NOT EXISTS idx_accounts_ft ON accounts(fetch_time);
CREATE INDEX IF NOT EXISTS idx_projects_ft ON projects(fetch_time);
CREATE INDEX IF NOT EXISTS idx_units_ft ON units(fetch_time);
CREATE INDEX IF NOT EXISTS idx_fetch_log_time ON fetch_log(fetch_time);
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

    # ── 写入 ──

    def insert_accounts(self, org_name: str, app_name: str, fetch_time: str, rows: list[dict]):
        for r in rows:
            self.conn.execute(
                "INSERT INTO accounts (org_name, app_name, fetch_time, account_name, account_id, account_status, "
                "account_budget, cost, daily_roi, daily_pay_amount, impressions, clicks, conversions, avg_conversion_cost) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (org_name, app_name, fetch_time, r.get("account_name"), r.get("account_id"), r.get("account_status"),
                 r.get("account_budget"), r.get("cost"), r.get("daily_roi"), r.get("daily_pay_amount"),
                 r.get("impressions"), r.get("clicks"), r.get("conversions"), r.get("avg_conversion_cost")),
            )
        self.conn.commit()
        logger.info(f"inserted {len(rows)} accounts at {fetch_time}")

    def insert_projects(self, org_name: str, app_name: str, fetch_time: str, rows: list[dict]):
        for r in rows:
            self.conn.execute(
                "INSERT INTO projects (org_name, app_name, fetch_time, project_name, project_id, status, "
                "project_budget, cost, daily_roi, impressions, conversions, avg_conversion_cost) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (org_name, app_name, fetch_time, r.get("project_name"), r.get("project_id"), r.get("status"),
                 r.get("project_budget"), r.get("cost"), r.get("daily_roi"),
                 r.get("impressions"), r.get("conversions"), r.get("avg_conversion_cost")),
            )
        self.conn.commit()
        logger.info(f"inserted {len(rows)} projects at {fetch_time}")

    def insert_units(self, org_name: str, app_name: str, fetch_time: str, rows: list[dict]):
        for r in rows:
            self.conn.execute(
                "INSERT INTO units (org_name, app_name, fetch_time, unit_name, unit_id, status, "
                "cost, daily_roi, daily_pay_amount, impressions, clicks, conversions, avg_conversion_cost) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (org_name, app_name, fetch_time, r.get("unit_name"), r.get("unit_id"), r.get("status"),
                 r.get("cost"), r.get("daily_roi"), r.get("daily_pay_amount"),
                 r.get("impressions"), r.get("clicks"), r.get("conversions"), r.get("avg_conversion_cost")),
            )
        self.conn.commit()
        logger.info(f"inserted {len(rows)} units at {fetch_time}")

    def create_fetch_log(self, org_name: str, app_name: str, fetch_time: str,
                         account_count: int, project_count: int, unit_count: int):
        self.conn.execute(
            "INSERT INTO fetch_log (org_name, app_name, fetch_time, account_count, project_count, unit_count) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (org_name, app_name, fetch_time, account_count, project_count, unit_count),
        )
        self.conn.commit()

    # ── 查询：最新数据（兼容规则引擎） ──

    def get_latest_data(self) -> dict:
        """获取最近一轮抓取的所有数据"""
        row = self.conn.execute("SELECT MAX(fetch_time) FROM fetch_log").fetchone()
        if not row or not row[0]:
            return {}

        latest_time = row[0]
        # 同一轮抓取：最近5分钟内的所有 fetch_time
        times = self.conn.execute(
            "SELECT DISTINCT fetch_time FROM fetch_log "
            "WHERE fetch_time >= datetime(?, '-5 minutes') ORDER BY fetch_time",
            (latest_time,),
        ).fetchall()
        if not times:
            return {}

        time_list = [t[0] for t in times]
        ph = ",".join("?" * len(time_list))

        result = {"accounts": [], "projects": [], "units": []}

        self.conn.row_factory = sqlite3.Row
        for row in self.conn.execute(
            f"SELECT * FROM accounts WHERE fetch_time IN ({ph})", time_list,
        ).fetchall():
            result["accounts"].append(dict(row))

        for row in self.conn.execute(
            f"SELECT * FROM projects WHERE fetch_time IN ({ph})", time_list,
        ).fetchall():
            result["projects"].append(dict(row))

        for row in self.conn.execute(
            f"SELECT * FROM units WHERE fetch_time IN ({ph})", time_list,
        ).fetchall():
            result["units"].append(dict(row))

        self.conn.row_factory = None
        return result

    # ── 查询：时间序列 ──

    def get_time_series(self, table: str, name: str,
                        start_time: str = None, end_time: str = None) -> list[dict]:
        """查询某个账户/项目/单元在时间范围内的所有快照，用于绘制变化曲线"""
        name_col = {"accounts": "account_name", "projects": "project_name", "units": "unit_name"}
        col = name_col.get(table)
        if not col:
            return []

        sql = f"SELECT * FROM {table} WHERE {col} = ?"
        params = [name]
        if start_time:
            sql += " AND fetch_time >= ?"
            params.append(start_time)
        if end_time:
            sql += " AND fetch_time <= ?"
            params.append(end_time)
        sql += " ORDER BY fetch_time"

        self.conn.row_factory = sqlite3.Row
        rows = self.conn.execute(sql, params).fetchall()
        self.conn.row_factory = None
        return [dict(r) for r in rows]

    def get_all_fetch_times(self, date: str = None) -> list[str]:
        """查询所有抓取时间点，可选按日期过滤（格式 '2026-03-10'）"""
        if date:
            rows = self.conn.execute(
                "SELECT DISTINCT fetch_time FROM fetch_log "
                "WHERE fetch_time LIKE ? ORDER BY fetch_time",
                (f"{date}%",),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT DISTINCT fetch_time FROM fetch_log ORDER BY fetch_time"
            ).fetchall()
        return [r[0] for r in rows]

    def close(self):
        self.conn.close()
