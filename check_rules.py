"""工具3：检查规则并发送飞书通知"""
import json
import logging
import os
import sys
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.db_manager import DBManager
from src.rules.rule_engine import load_rules, run_rules
from src.notification.feishu import send_feishu

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler("logs/check_rules.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    db_path = config["database"]["path"]
    webhook_url = config["feishu"]["webhook_url"]

    os.makedirs("logs", exist_ok=True)

    output = {"status": "ok", "triggered_count": 0, "rules": []}

    db = DBManager(db_path)
    try:
        # 1. 获取最新一轮数据
        data = db.get_latest_data()
        if not data:
            logger.warning("no data found in database")
            output["status"] = "no_data"
            print(json.dumps(output, ensure_ascii=False))
            return

        logger.info(
            f"loaded latest data: "
            f"accounts={len(data['accounts'])}, "
            f"projects={len(data['projects'])}, "
            f"units={len(data['units'])}"
        )

        # 2. 加载并执行规则
        rules = load_rules()
        if not rules:
            logger.info("no enabled rules found")
            output["status"] = "no_rules"
            print(json.dumps(output, ensure_ascii=False))
            return

        results = run_rules(rules, data, db)
        output["rules"] = results
        output["triggered_count"] = sum(1 for r in results if r["triggered"])

        # 3. 发送通知（只发触发的规则）
        all_messages = []
        for r in results:
            if r["triggered"]:
                all_messages.extend(r["messages"])

        if all_messages:
            logger.info(f"total {len(all_messages)} messages to send")
            send_feishu(webhook_url, all_messages)
        else:
            logger.info("no rules triggered, no notification")

        # 4. 输出结构化结果到 stdout
        print(json.dumps(output, ensure_ascii=False))

    except Exception as e:
        logger.error(f"check_rules failed: {e}", exc_info=True)
        output["status"] = "error"
        output["error"] = str(e)
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
