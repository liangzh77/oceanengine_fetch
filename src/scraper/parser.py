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
    "计费当日付费ROI": "daily_roi",
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

# 状态字段映射
STATUS_FIELDS = {"account_status", "status"}
# 名称字段（保留原文本）
NAME_FIELDS = {"account_name", "project_name", "unit_name", "account_status", "status"}
# ID 字段（保留原文本）
ID_FIELDS = {"account_id", "project_id", "unit_id"}

# 只保留这些状态的数据
ACTIVE_STATUSES = {"启用中", "审核通过", "投放中"}


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


def _normalize(s: str) -> str:
    """去除空格、换行，统一用于模糊匹配列名"""
    return re.sub(r'\s+', '', s)


def _build_col_mapping(raw_cols: list[str], field_map: dict) -> dict:
    """构建 Excel 实际列名 → db_field 的映射，支持模糊匹配"""
    # 先建一个 normalized_key → (raw_key, db_field) 的查找表
    norm_map = {_normalize(k): (k, v) for k, v in field_map.items()}
    col_mapping = {}  # excel_col -> db_field
    matched_keys = set()

    for col in raw_cols:
        if not col:
            continue
        norm_col = _normalize(col)
        if norm_col in norm_map:
            _, db_field = norm_map[norm_col]
            col_mapping[col] = db_field
            matched_keys.add(norm_col)

    # 记录未匹配的期望字段
    unmatched = [k for nk, (k, v) in norm_map.items() if nk not in matched_keys]
    if unmatched:
        logger.warning(f"Excel 中未找到以下列: {unmatched}，实际列名: {raw_cols}")

    return col_mapping


def _parse_rows(raw_rows: list[dict], field_map: dict, status_field: str) -> list[dict]:
    """通用解析：根据 field_map 映射列名，只保留启用中的数据"""
    if not raw_rows:
        return []

    # 用第一行的 key 构建列名映射
    col_mapping = _build_col_mapping(list(raw_rows[0].keys()), field_map)

    parsed = []
    for raw in raw_rows:
        record = {}
        for excel_col, db_field in col_mapping.items():
            value = raw.get(excel_col)
            if db_field in NAME_FIELDS or db_field in ID_FIELDS:
                record[db_field] = str(value).strip() if value else ""
            else:
                record[db_field] = _parse_number(value)

        # 只保留启用中的数据
        status = record.get(status_field, "")
        if status not in ACTIVE_STATUSES:
            continue

        parsed.append(record)
    return parsed


def parse_accounts(raw_rows: list[dict]) -> list[dict]:
    return _parse_rows(raw_rows, ACCOUNT_FIELD_MAP, "account_status")


def parse_projects(raw_rows: list[dict]) -> list[dict]:
    return _parse_rows(raw_rows, PROJECT_FIELD_MAP, "status")


def parse_units(raw_rows: list[dict]) -> list[dict]:
    return _parse_rows(raw_rows, UNIT_FIELD_MAP, "status")
