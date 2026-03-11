"""数据解析模块：将 Excel 下载数据映射为数据库字段"""
import logging
import re

logger = logging.getLogger(__name__)

ACCOUNT_FIELD_MAP = {
    "账户信息": "account_name",
    "账户ID": "account_id",
    "账户状态": "account_status",
    "账户预算": "account_budget",
    "消耗": "cost",
    "当日付费ROI": "daily_roi",
    "计费当日付费金额": "daily_pay_amount",
    "展示数": "impressions",
    "点击数": "clicks",
    "转化数": "conversions",
    "平均转化成本": "avg_conversion_cost",
}

PROJECT_FIELD_MAP = {
    "项目信息": "project_name",
    "项目ID": "project_id",
    "项目一级状态": "status",
    "项目预算": "project_budget",
    "消耗": "cost",
    "当日付费ROI": "daily_roi",
    "展示数": "impressions",
    "转化数": "conversions",
    "平均转化成本": "avg_conversion_cost",
}

UNIT_FIELD_MAP = {
    "单元信息": "unit_name",
    "单元ID": "unit_id",
    "投放一级状态名称": "status",
    "消耗": "cost",
    "当日付费ROI": "daily_roi",
    "当日付费金额": "daily_pay_amount",
    "展示数": "impressions",
    "点击数": "clicks",
    "转化数": "conversions",
    "平均转化成本": "avg_conversion_cost",
}

# 名称字段（保留原文本）
NAME_FIELDS = {"account_name", "project_name", "unit_name", "account_status", "status"}
# ID 字段（保留原文本）
ID_FIELDS = {"account_id", "project_id", "unit_id"}


def _parse_number(value):
    """解析数值字段，返回 float 或 None"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip()
    if not value or value in ("--", "—", ""):
        return None
    value = value.replace(",", "").replace("%", "")
    if re.search(r'[^\d.\-]', value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_rows(raw_rows: list[dict], field_map: dict) -> list[dict]:
    """通用解析：根据 field_map 映射列名"""
    parsed = []
    for raw in raw_rows:
        record = {}
        for raw_col, db_field in field_map.items():
            value = raw.get(raw_col)
            if db_field in NAME_FIELDS or db_field in ID_FIELDS:
                record[db_field] = str(value).strip() if value else ""
            else:
                record[db_field] = _parse_number(value)
        parsed.append(record)
    return parsed


def parse_accounts(raw_rows: list[dict]) -> list[dict]:
    return _parse_rows(raw_rows, ACCOUNT_FIELD_MAP)


def parse_projects(raw_rows: list[dict]) -> list[dict]:
    return _parse_rows(raw_rows, PROJECT_FIELD_MAP)


def parse_units(raw_rows: list[dict]) -> list[dict]:
    return _parse_rows(raw_rows, UNIT_FIELD_MAP)
