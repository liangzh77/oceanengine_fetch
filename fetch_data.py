"""工具1：抓取巨量引擎广告数据并存入数据库"""
import argparse
import logging
import os
import sys
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scraper.browser import BrowserManager
from src.scraper.extractor import DataExtractor
from src.scraper.parser import parse_accounts, parse_projects, parse_units
from src.database.db_manager import DBManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/fetch_data.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Fetch OceanEngine ad data")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--login", action="store_true", help="Force re-login (delete saved auth)")
    args = parser.parse_args()

    config = load_config()
    url = config["url"]
    context_dir = config["browser"]["context_dir"]
    db_path = config["database"]["path"]

    os.makedirs("logs", exist_ok=True)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Force re-login if requested
    if args.login:
        auth_path = os.path.join(context_dir, "auth.json")
        if os.path.exists(auth_path):
            os.remove(auth_path)
            logger.info("auth.json deleted, will re-login")

    browser_mgr = BrowserManager(context_dir)
    db = DBManager(db_path)

    try:
        page = browser_mgr.start(headless=args.headless)
        browser_mgr.navigate_and_ensure_login(url, timeout=300)
        page.wait_for_timeout(5000)

        extractor = DataExtractor(page)
        orgs = config["organizations"]

        for org in orgs:
            org_name = org["name"]
            app_name = org["app_name"]
            logger.info(f"=== Processing: {org_name} - {app_name} ===")

            extractor.switch_organization(org_name, app_name)

            # Fetch raw data
            raw_accounts = extractor.fetch_accounts()
            raw_projects = extractor.fetch_projects()
            raw_units = extractor.fetch_units()

            # Parse
            accounts = parse_accounts(raw_accounts)
            projects = parse_projects(raw_projects)
            units = parse_units(raw_units)

            # Store
            batch_id = db.create_batch(org_name, app_name)
            db.insert_accounts(batch_id, accounts)
            db.insert_projects(batch_id, projects)
            db.insert_units(batch_id, units)

            logger.info(
                f"Done: {org_name}-{app_name} | "
                f"accounts={len(accounts)}, projects={len(projects)}, units={len(units)}"
            )

        logger.info("=== All organizations fetched successfully ===")

    except Exception as e:
        logger.error(f"Fetch failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()
        browser_mgr.close()


if __name__ == "__main__":
    main()
