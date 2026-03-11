"""示例规则：ROI 为 0 的项目报警
这是一个示例规则文件，展示规则的编写格式。
你可以复制此文件并修改 check() 函数来创建新规则。
"""

name = "示例：ROI为0的项目"
enabled = False  # 默认关闭，仅作示例


def check(data, db=None) -> list[str]:
    """
    检查数据，返回触发说明列表。
    - 空列表表示未触发
    - 每条字符串是一个触发说明，描述具体是什么情况触发了这条规则

    同一条规则可能因不同原因触发多次，每次返回不同的说明。
    例如：多个项目分别满足条件，每个项目生成一条说明。

    参数：
        data: 最新一轮抓取的数据快照
        db: 数据库实例，可查询历史数据

    data 结构：
    {
        "accounts": [{"org_name", "app_name", "fetch_time", "account_name", ...}, ...],
        "projects": [{"org_name", "app_name", "fetch_time", "project_name", ...}, ...],
        "units": [{"org_name", "app_name", "fetch_time", "unit_name", ...}, ...],
    }

    db 可用方法：
        db.get_time_series("projects", "项目名称")  -> 该项目所有时间点的快照列表
        db.get_all_fetch_times("2026-03-10")        -> 当天所有抓取时间点
    """
    messages = []
    for row in data.get("projects", []):
        if row.get("daily_roi") is not None and row["daily_roi"] == 0 and row.get("cost", 0) > 100:
            messages.append(f"项目 {row['project_name']} 消耗={row['cost']}元 但ROI=0")
    return messages
