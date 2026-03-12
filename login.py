"""工具3：手动登录巨量引擎，保存登录状态供 headless 抓取使用"""
import logging
import os
import sys
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scraper.browser import BrowserManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(stream=open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1))],
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    url = config["url"]
    context_dir = config["browser"]["context_dir"]

    browser_mgr = BrowserManager(context_dir)

    try:
        page = browser_mgr.start(headless=False)
        browser_mgr.navigate_and_ensure_login(url, timeout=600)
        logger.info("登录成功，登录状态已保存")
        logger.info("浏览器将在 10 秒后关闭...")
        page.wait_for_timeout(10000)

    except TimeoutError:
        logger.error("登录超时（600秒），请重试")
        sys.exit(1)
    except Exception as e:
        logger.error(f"登录失败: {e}", exc_info=True)
        sys.exit(1)
    finally:
        browser_mgr.close()


if __name__ == "__main__":
    main()
