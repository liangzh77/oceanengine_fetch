"""规则引擎：扫描 rules/ 目录，加载并执行所有规则"""
import importlib.util
import logging
import os

logger = logging.getLogger(__name__)

RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "rules")


def load_rules() -> list:
    """扫描 rules/ 目录，加载所有 enabled 的规则模块"""
    rules = []
    if not os.path.isdir(RULES_DIR):
        logger.warning(f"rules directory not found: {RULES_DIR}")
        return rules

    for filename in sorted(os.listdir(RULES_DIR)):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue

        filepath = os.path.join(RULES_DIR, filename)
        try:
            spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            if not getattr(mod, "enabled", True):
                logger.info(f"rule '{filename}' is disabled, skip")
                continue

            if not hasattr(mod, "check"):
                logger.warning(f"rule '{filename}' has no check() function, skip")
                continue

            rules.append({
                "name": getattr(mod, "name", filename),
                "file": filename,
                "check": mod.check,
            })
            logger.info(f"loaded rule: {getattr(mod, 'name', filename)} ({filename})")
        except Exception as e:
            logger.error(f"failed to load rule '{filename}': {e}")

    return rules


def run_rules(rules: list, data: dict, db=None) -> list[str]:
    """执行所有规则，返回触发的消息列表。db 可选，供规则查询��史数据。"""
    all_messages = []
    for rule in rules:
        try:
            messages = rule["check"](data, db)
            if messages:
                logger.info(f"rule '{rule['name']}' triggered: {len(messages)} messages")
                all_messages.extend(messages)
            else:
                logger.info(f"rule '{rule['name']}' not triggered")
        except Exception as e:
            logger.error(f"rule '{rule['name']}' execution error: {e}")
    return all_messages
