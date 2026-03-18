"""数据库管理模块：按天存储广告数据，重复抓取自动覆盖更新（UPSERT）"""
import logging
import sqlite3
from datetime import date as _date, timedelta

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS fetch_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    org_name    TEXT NOT NULL,
    app_name    TEXT NOT NULL,
    date        TEXT NOT NULL,
    account_count  INTEGER DEFAULT 0,
    project_count  INTEGER DEFAULT 0,
    unit_count     INTEGER DEFAULT 0,
    UNIQUE (org_name, app_name, date)
);

CREATE TABLE IF NOT EXISTS accounts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    org_name        TEXT NOT NULL,
    app_name        TEXT NOT NULL,
    date            TEXT NOT NULL,
    account_name    TEXT,
    account_id      TEXT,
    account_status  TEXT,
    account_budget  REAL,
    cost            REAL,
    daily_roi       REAL,
    daily_pay_amount REAL,
    impressions     REAL,
    clicks          REAL,
    conversions     REAL,
    avg_conversion_cost REAL,
    UNIQUE (org_name, app_name, date, account_id)
);

CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    org_name        TEXT NOT NULL,
    app_name        TEXT NOT NULL,
    date            TEXT NOT NULL,
    project_name    TEXT,
    project_id      TEXT,
    status          TEXT,
    project_budget  REAL,
    cost            REAL,
    daily_roi       REAL,
    impressions     REAL,
    conversions     REAL,
    avg_conversion_cost REAL,
    UNIQUE (org_name, app_name, date, project_id)
);

CREATE TABLE IF NOT EXISTS units (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    org_name        TEXT NOT NULL,
    app_name        TEXT NOT NULL,
    date            TEXT NOT NULL,
    unit_name       TEXT,
    unit_id         TEXT,
    status          TEXT,
    cost            REAL,
    daily_roi       REAL,
    daily_pay_amount REAL,
    impressions     REAL,
    clicks          REAL,
    conversions     REAL,
    avg_conversion_cost REAL,
    UNIQUE (org_name, app_name, date, unit_id)
);

CREATE INDEX IF NOT EXISTS idx_accounts_date   ON accounts(date);
CREATE INDEX IF NOT EXISTS idx_accounts_app    ON accounts(app_name, date);
CREATE INDEX IF NOT EXISTS idx_projects_date   ON projects(date);
CREATE INDEX IF NOT EXISTS idx_projects_app    ON projects(app_name, date);
CREATE INDEX IF NOT EXISTS idx_units_date      ON units(date);
CREATE INDEX IF NOT EXISTS idx_units_app       ON units(app_name, date);
CREATE INDEX IF NOT EXISTS idx_fetch_log_date  ON fetch_log(date);
"""


def offset_to_date(day_offset: int = 0) -> str:
    """将天数偏移转为日期字符串，0=今天，-1=昨天"""
    return (_date.today() + timedelta(days=day_offset)).strftime("%Y-%m-%d")


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

    # ── 写入（UPSERT：同一天同一广告单元只保留最新值）──

    def upsert_accounts(self, org_name: str, app_name: str, date: str, rows: list[dict]):
        for r in rows:
            self.conn.execute(
                "INSERT INTO accounts "
                "(org_name, app_name, date, account_name, account_id, account_status, "
                "account_budget, cost, daily_roi, daily_pay_amount, impressions, clicks, "
                "conversions, avg_conversion_cost) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(org_name, app_name, date, account_id) DO UPDATE SET "
                "account_name=excluded.account_name, account_status=excluded.account_status, "
                "account_budget=excluded.account_budget, cost=excluded.cost, "
                "daily_roi=excluded.daily_roi, daily_pay_amount=excluded.daily_pay_amount, "
                "impressions=excluded.impressions, clicks=excluded.clicks, "
                "conversions=excluded.conversions, avg_conversion_cost=excluded.avg_conversion_cost",
                (org_name, app_name, date,
                 r.get("account_name"), r.get("account_id"), r.get("account_status"),
                 r.get("account_budget"), r.get("cost"), r.get("daily_roi"),
                 r.get("daily_pay_amount"), r.get("impressions"), r.get("clicks"),
                 r.get("conversions"), r.get("avg_conversion_cost")),
            )
        self.conn.commit()
        logger.info(f"upserted {len(rows)} accounts for {date}")

    def upsert_projects(self, org_name: str, app_name: str, date: str, rows: list[dict]):
        for r in rows:
            self.conn.execute(
                "INSERT INTO projects "
                "(org_name, app_name, date, project_name, project_id, status, "
                "project_budget, cost, daily_roi, impressions, conversions, avg_conversion_cost) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(org_name, app_name, date, project_id) DO UPDATE SET "
                "project_name=excluded.project_name, status=excluded.status, "
                "project_budget=excluded.project_budget, cost=excluded.cost, "
                "daily_roi=excluded.daily_roi, impressions=excluded.impressions, "
                "conversions=excluded.conversions, avg_conversion_cost=excluded.avg_conversion_cost",
                (org_name, app_name, date,
                 r.get("project_name"), r.get("project_id"), r.get("status"),
                 r.get("project_budget"), r.get("cost"), r.get("daily_roi"),
                 r.get("impressions"), r.get("conversions"), r.get("avg_conversion_cost")),
            )
        self.conn.commit()
        logger.info(f"upserted {len(rows)} projects for {date}")

    def upsert_units(self, org_name: str, app_name: str, date: str, rows: list[dict]):
        for r in rows:
            self.conn.execute(
                "INSERT INTO units "
                "(org_name, app_name, date, unit_name, unit_id, status, "
                "cost, daily_roi, daily_pay_amount, impressions, clicks, "
                "conversions, avg_conversion_cost) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(org_name, app_name, date, unit_id) DO UPDATE SET "
                "unit_name=excluded.unit_name, status=excluded.status, "
                "cost=excluded.cost, daily_roi=excluded.daily_roi, "
                "daily_pay_amount=excluded.daily_pay_amount, impressions=excluded.impressions, "
                "clicks=excluded.clicks, conversions=excluded.conversions, "
                "avg_conversion_cost=excluded.avg_conversion_cost",
                (org_name, app_name, date,
                 r.get("unit_name"), r.get("unit_id"), r.get("status"),
                 r.get("cost"), r.get("daily_roi"), r.get("daily_pay_amount"),
                 r.get("impressions"), r.get("clicks"),
                 r.get("conversions"), r.get("avg_conversion_cost")),
            )
        self.conn.commit()
        logger.info(f"upserted {len(rows)} units for {date}")

    def upsert_fetch_log(self, org_name: str, app_name: str, date: str,
                         account_count: int, project_count: int, unit_count: int):
        self.conn.execute(
            "INSERT INTO fetch_log (org_name, app_name, date, account_count, project_count, unit_count) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(org_name, app_name, date) DO UPDATE SET "
            "account_count=excluded.account_count, "
            "project_count=excluded.project_count, "
            "unit_count=excluded.unit_count",
            (org_name, app_name, date, account_count, project_count, unit_count),
        )
        self.conn.commit()

    # ── 查询 ──

    def get_data_by_date(self, date: str) -> dict:
        """获取指定日期的全部数据"""
        self.conn.row_factory = sqlite3.Row
        result = {
            "accounts": [dict(r) for r in self.conn.execute(
                "SELECT * FROM accounts WHERE date=?", (date,)).fetchall()],
            "projects": [dict(r) for r in self.conn.execute(
                "SELECT * FROM projects WHERE date=?", (date,)).fetchall()],
            "units": [dict(r) for r in self.conn.execute(
                "SELECT * FROM units WHERE date=?", (date,)).fetchall()],
        }
        self.conn.row_factory = None
        return result

    def get_available_dates(self) -> list[str]:
        """返回数据库中所有有数据的日期列表"""
        rows = self.conn.execute(
            "SELECT DISTINCT date FROM fetch_log ORDER BY date DESC"
        ).fetchall()
        return [r[0] for r in rows]

    def query(self,
              table: str,
              date: str = None,
              app_names: list[str] = None,
              name_keywords: list[str] = None) -> list[dict]:
        """
        通用查询接口
        :param table:         'accounts' | 'projects' | 'units'
        :param date:          日期字符串 'YYYY-MM-DD'，None 则不过滤
        :param app_names:     按产品（app_name）过滤，None 则不过滤
        :param name_keywords: 按名称模糊匹配，None 则不过滤
        """
        name_col = {"accounts": "account_name", "projects": "project_name", "units": "unit_name"}
        col = name_col.get(table)
        if not col:
            return []

        sql = f"SELECT * FROM {table} WHERE 1=1"
        params: list = []

        if date:
            sql += " AND date=?"
            params.append(date)

        if app_names:
            ph = ",".join("?" * len(app_names))
            sql += f" AND app_name IN ({ph})"
            params.extend(app_names)

        if name_keywords:
            kw_clauses = " OR ".join([f"{col} LIKE ?" for _ in name_keywords])
            sql += f" AND ({kw_clauses})"
            params.extend([f"%{k}%" for k in name_keywords])

        sql += f" ORDER BY app_name, {col}"

        self.conn.row_factory = sqlite3.Row
        rows = self.conn.execute(sql, params).fetchall()
        self.conn.row_factory = None
        return [dict(r) for r in rows]

    def close(self):
        self.conn.close()
