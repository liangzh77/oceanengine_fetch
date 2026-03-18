"""tools/query_data.py - 查询广告数据库，输出 JSON

用法示例:
    python tools/query_data.py                          # 昨天全部数据
    python tools/query_data.py --day 0                  # 今天全部数据
    python tools/query_data.py --date 2026-03-15        # 指定日期全部数据
    python tools/query_data.py --day -1 --products 缘话app --table accounts
    python tools/query_data.py --day -1 --accounts 测试账户
    python tools/query_data.py --day -1 --projects 春节推广
    python tools/query_data.py --day -1 --units 视频单元A 视频单元B
    python tools/query_data.py --list-dates           # 列出所有有数据的日期
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import yaml
from src.database.db_manager import DBManager, offset_to_date


def load_config() -> dict:
    config_path = os.path.join(ROOT, "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="查询广告数据库")
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument(
        "--day", type=int, default=None,
        help="天数偏移：0=今天，-1=昨天（默认 -1）"
    )
    date_group.add_argument(
        "--date", type=str, default=None,
        help="指定日期，格式 YYYY-MM-DD"
    )

    parser.add_argument(
        "--table", choices=["accounts", "projects", "units", "all"], default="all",
        help="查询哪张表（默认 all）"
    )
    parser.add_argument(
        "--products", nargs="+", default=None,
        metavar="APP_NAME",
        help="按产品（app_name）过滤，例如 --products 缘话app 丝话app"
    )
    parser.add_argument(
        "--accounts", nargs="+", default=None,
        metavar="KEYWORD",
        help="按账户名关键词模糊匹配"
    )
    parser.add_argument(
        "--projects", nargs="+", default=None,
        metavar="KEYWORD",
        help="按项目名关键词模糊匹配"
    )
    parser.add_argument(
        "--units", nargs="+", default=None,
        metavar="KEYWORD",
        help="按单元名关键词模糊匹配"
    )
    parser.add_argument(
        "--list-dates", action="store_true",
        help="列出数据库中所有有数据的日期"
    )

    args = parser.parse_args()

    config = load_config()
    db_path = os.path.join(ROOT, config["database"]["path"])
    db = DBManager(db_path)

    try:
        # 仅列出日期
        if args.list_dates:
            dates = db.get_available_dates()
            output = {"dates": dates}
            print(json.dumps(output, ensure_ascii=False))
            return

        # 解析目标日期
        if args.date:
            target_date = args.date
        elif args.day is not None:
            target_date = offset_to_date(args.day)
        else:
            target_date = offset_to_date(-1)  # 默认昨天

        # 决定要查哪些表
        tables_to_query = (
            ["accounts", "projects", "units"] if args.table == "all" else [args.table]
        )

        keyword_map = {
            "accounts": args.accounts,
            "projects": args.projects,
            "units": args.units,
        }

        output = {"date": target_date}

        for tbl in tables_to_query:
            rows = db.query(
                table=tbl,
                date=target_date,
                app_names=args.products,
                name_keywords=keyword_map.get(tbl),
            )
            output[tbl] = rows

        print(json.dumps(output, ensure_ascii=False))

    finally:
        db.close()


if __name__ == "__main__":
    main()
