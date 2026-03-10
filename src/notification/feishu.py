"""飞书 Webhook 通知"""
import json
import logging
import requests

logger = logging.getLogger(__name__)


def send_feishu(webhook_url: str, messages: list[str]):
    """发送飞书通知，将多条消息合并为一条"""
    if not webhook_url:
        logger.warning("feishu webhook_url is empty, skip notification")
        return
    if not messages:
        return

    text = "\n".join(messages)
    payload = {
        "msg_type": "text",
        "content": {"text": f"[巨量引擎监控]\n{text}"},
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                logger.info(f"feishu notification sent: {len(messages)} messages")
            else:
                logger.error(f"feishu API error: {data}")
        else:
            logger.error(f"feishu HTTP error: {resp.status_code}")
    except Exception as e:
        logger.error(f"feishu send failed: {e}")
