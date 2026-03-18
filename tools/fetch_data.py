"""tools/fetch_data.py - 抓取巨量引擎广告数据，按天存入数据库（UPSERT）

用法:
    python tools/fetch_data.py           # 抓取今天数据（默认 --day 0）
    python tools/fetch_data.py --day -1  # 抓取昨天数据
    python tools/fetch_data.py --headless --day 0
    python tools/fetch_data.py --login   # 强制重新登录
"""
import argparse
import logging
import os
import sys
import time
import yaml

# 确保根目录在路径中
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.database.db_manager import DBManager, offset_to_date
from src.scraper.browser import BrowserManager, AuthExpiredError
from src.scraper.extractor import DataExtractor
from src.scraper.parser import parse_accounts, parse_projects, parse_units

os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(
            stream=open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)
        ),
        logging.FileHandler(
            os.path.join(ROOT, "logs", "fetch_data.log"), encoding="utf-8"
        ),
    ],
)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 5 * 60  # 5 分钟


def load_config() -> dict:
    config_path = os.path.join(ROOT, "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def do_fetch(config: dict, target_date: str, headless: bool, force_login: bool) -> None:
    """执行一次完整抓取，成功则正常返回，失败抛出异常"""
    context_dir = os.path.join(ROOT, config["browser"]["context_dir"])
    db_path = os.path.join(ROOT, config["database"]["path"])
    url = config["url"]

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if force_login:
        auth_path = os.path.join(context_dir, "auth.json")
        if os.path.exists(auth_path):
            os.remove(auth_path)
            logger.info("auth.json deleted, will re-login")

    browser_mgr = BrowserManager(context_dir)
    db = DBManager(db_path)

    try:
        browser_mgr.start(headless=headless)
        browser_mgr.navigate_and_ensure_login(url, timeout=300)
        browser_mgr.page.wait_for_timeout(5000)

        extractor = DataExtractor(browser_mgr.page)
        orgs = config["organizations"]

        for org in orgs:
            org_name = org["name"]
            app_name = org["app_name"]
            logger.info(f"=== Processing: {org_name} - {app_name} ({target_date}) ===")

            extractor.switch_organization(org_name, app_name)
            extractor.set_date_filter(target_date)

            accounts = parse_accounts(extractor.fetch_accounts())
            db.upsert_accounts(org_name, app_name, target_date, accounts)
            logger.info(f"accounts written: {len(accounts)}")

            projects = parse_projects(extractor.fetch_projects())
            db.upsert_projects(org_name, app_name, target_date, projects)
            logger.info(f"projects written: {len(projects)}")

            units = parse_units(extractor.fetch_units())
            db.upsert_units(org_name, app_name, target_date, units)
            logger.info(f"units written: {len(units)}")

            db.upsert_fetch_log(
                org_name, app_name, target_date,
                len(accounts), len(projects), len(units)
            )

            logger.info(
                f"Done: {org_name}-{app_name} | "
                f"accounts={len(accounts)}, projects={len(projects)}, units={len(units)}"
            )

        logger.info(f"=== All organizations fetched for {target_date} ===")

    finally:
        db.close()
        browser_mgr.close()


def main():
    parser = argparse.ArgumentParser(description="抓取巨量引擎广告数据")
    parser.add_argument(
        "--day", type=int, default=0,
        help="抓取哪一天的数据：0=今天，-1=昨天（默认 0）"
    )
    parser.add_argument("--headless", action="store_true", help="无头模式运行浏览器")
    parser.add_argument("--login", action="store_true", help="强制重新登录")
    args = parser.parse_args()

    config = load_config()
    target_date = offset_to_date(args.day)
    logger.info(f"目标日期: {target_date}")

    attempt = 0
    last_error = None

    while attempt < MAX_RETRIES:
        attempt += 1
        logger.info(f"第 {attempt}/{MAX_RETRIES} 次尝试...")
        try:
            do_fetch(config, target_date, headless=args.headless, force_login=(args.login and attempt == 1))
            print(f"SUCCESS: {target_date} 数据抓取完成")
            sys.exit(0)

        except AuthExpiredError as e:
            # 认证失效不重试
            msg = f"AUTH_EXPIRED: {e}"
            logger.error(msg)
            print(f"FAILED: {msg}")
            sys.exit(2)

        except (TimeoutError, ConnectionError, OSError) as e:
            # 网络/超时类错误，等待后重试
            last_error = e
            logger.warning(f"网络/超时错误: {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"将在 {RETRY_WAIT_SECONDS // 60} 分钟后重试...")
                time.sleep(RETRY_WAIT_SECONDS)

        except Exception as e:
            # 其他错误也重试（可能是页面临时异常）
            last_error = e
            logger.error(f"抓取失败: {e}", exc_info=True)
            if attempt < MAX_RETRIES:
                logger.info(f"将在 {RETRY_WAIT_SECONDS // 60} 分钟后重试...")
                time.sleep(RETRY_WAIT_SECONDS)

    msg = f"连续 {MAX_RETRIES} 次抓取失败，最后错误: {last_error}"
    logger.error(msg)
    print(f"FAILED: {msg}")
    sys.exit(1)


if __name__ == "__main__":
    main()
