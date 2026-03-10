"""数据解析模块：将原始抓取数据映射为干净的数据库字段"""
import json
import logging
import re

logger = logging.getLogger(__name__)

ACCOUNT_FIELD_MAP = {
    "账户信息": "account_name",
    "账户预算": "account_budget",
    "消耗(元)": "cost",
    "当日付费ROI": "daily_roi",
}

PROJECT_FIELD_MAP = {
    "项目信息": "project_name",
    "项目预算": "project_budget",
    "消耗(元)": "cost",
    "当日付费ROI": "daily_roi",
    "项目状态": "status",
}

UNIT_FIELD_MAP = {
    "单元信息": "unit_name",
    "消耗(元)": "cost",
    "当日付费ROI": "daily_roi",
    "投放状态": "status",
}


def _parse_number(value: str):
    """解析数值字段，返回 float 或 None"""
    if not value or value in ("--", "—", ""):
        return None
    # 去掉逗号
    value = value.replace(",", "")
    # "不��预算" 等非数字
    if re.search(r'[^\d.\-]', value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _extract_name(value: str) -> str:
    """从多行文本中提取名称（第一行），去掉 ID 行"""
    if not value:
        return ""
    lines = [l.strip() for l in value.split("\n") if l.strip()]
    if not lines:
        return ""
    # 过滤掉 "ID：xxx" 行
    name_lines = [l for l in lines if not l.startswith("ID：") and not l.startswith("ID:")]
    return name_lines[0] if name_lines else lines[0]


def _parse_rows(raw_rows: list[dict], field_map: dict, name_fields: set) -> list[dict]:
    """通用解析：根据 field_map 映射列名，解析数值"""
    parsed = []
    for raw in raw_rows:
        record = {}
        for raw_col, db_field in field_map.items():
            value = raw.get(raw_col, "")
            if db_field in name_fields:
                record[db_field] = _extract_name(value)
            else:
                record[db_field] = _parse_number(value)
        record["raw_data"] = json.dumps(raw, ensure_ascii=False)
        parsed.append(record)
    return parsed


def parse_accounts(raw_rows: list[dict]) -> list[dict]:
    return _parse_rows(raw_rows, ACCOUNT_FIELD_MAP, {"account_name"})


def parse_projects(raw_rows: list[dict]) -> list[dict]:
    return _parse_rows(raw_rows, PROJECT_FIELD_MAP, {"project_name", "status"})


def parse_units(raw_rows: list[dict]) -> list[dict]:
    return _parse_rows(raw_rows, UNIT_FIELD_MAP, {"unit_name", "status"})
