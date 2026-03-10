"""示例规则：ROI 为 0 的项目报警
这是一个示例规则文件，展示规则的编写格式。
你可以复制此文件并修改 check() 函数来创建新规则。
"""

name = "示例：ROI为0的项目"
enabled = False  # 默认关闭，仅作示例


def check(data) -> list[str]:
    """
    检查数据，返回需要通知的消息列表。
    空列表表示不触发通知。

    data 结构：
    {
        "batches": [{"batch_id", "org_name", "app_name", "fetch_time"}, ...],
        "accounts": [{"batch_id", "account_name", "account_budget", "cost", "daily_roi"}, ...],
        "projects": [{"batch_id", "project_name", "project_budget", "cost", "daily_roi", "status", "bid_price"}, ...],
        "units": [{"batch_id", "unit_name", "cost", "daily_roi", "status"}, ...],
    }
    """
    messages = []
    for row in data.get("projects", []):
        if row.get("daily_roi") is not None and row["daily_roi"] == 0 and row.get("cost", 0) > 100:
            messages.append(f"项目 {row['project_name']} 消耗={row['cost']}元 但ROI=0")
    return messages
