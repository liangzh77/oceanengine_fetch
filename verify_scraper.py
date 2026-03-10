"""验证脚本：完整抓取验证"""
import sys
import os
import json
import logging
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.scraper.browser import BrowserManager
from src.scraper.extractor import DataExtractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

VERIFY_TARGETS = {
    "account": "民众-伊心-缘话-安卓-每次付费-UBA-05-在投",
    "project": "缘话-伊心-每次-3.4-勇-中年",
    "unit": "缘话-伊心-每次-3.4-勇-中年_居家风韵-1535_1",
}


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    url = config["url"]
    context_dir = config["browser"]["context_dir"]
    browser_mgr = BrowserManager(context_dir)
    os.makedirs("logs", exist_ok=True)

    try:
        page = browser_mgr.start(headless=False)
        browser_mgr.navigate_and_ensure_login(url, timeout=300)
        page.wait_for_timeout(5000)

        extractor = DataExtractor(page)

        # Step 1: Fetch data from current org (already on 缘话app)
        logger.info("=== Fetching data from current page ===")
        page.screenshot(path="logs/before_fetch.png")

        data = extractor.fetch_all()

        # Save raw data
        with open("logs/fetched_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Data saved to logs/fetched_data.json")

        # Step 2: Verify targets
        logger.info("=== Verification ===")
        logger.info(f"accounts: {len(data['accounts'])} rows")
        logger.info(f"projects: {len(data['projects'])} rows")
        logger.info(f"units: {len(data['units'])} rows")

        # Check account
        acct_found = any(
            VERIFY_TARGETS["account"] in str(row)
            for row in data["accounts"]
        )
        logger.info(f"account target found: {acct_found}")

        # Check project
        proj_found = any(
            VERIFY_TARGETS["project"] in str(row)
            for row in data["projects"]
        )
        logger.info(f"project target found: {proj_found}")

        # Check unit
        unit_found = any(
            VERIFY_TARGETS["unit"] in str(row)
            for row in data["units"]
        )
        logger.info(f"unit target found: {unit_found}")

        if acct_found and proj_found and unit_found:
            logger.info("ALL TARGETS FOUND - verification PASSED!")
        else:
            logger.warning("Some targets NOT found - check logs/fetched_data.json")

        page.screenshot(path="logs/after_fetch.png")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        browser_mgr.close()


if __name__ == "__main__":
    main()
