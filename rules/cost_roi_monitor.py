"""巨量引擎消耗与ROI监控规则

监控规则：
1. 消耗 < 2000元：不关注
2. 消耗 >= 2000元 且 ROI < 0.09：关注并提醒限额到4000
3. 已限额账户：消耗占比 >= 80% 且 ROI符合下一放量额度：重点提醒和关注
"""

name = "消耗与ROI监控规则"
enabled = True


def check(data, db=None) -> list[str]:
    """
    检查消耗与ROI规则
    
    限额档位参考：
    - 限额4000元 → 下一放量额度 ROI >= 0.09
    - 限额8000元 → 下一放量额度 ROI >= 0.10
    - 限额15000元 → 下一放量额度 ROI >= 0.11
    - 更高额度 → ROI >= 0.12
    """
    messages = []
    
    # 限额档位配置
    quota_tiers = [
        (4000, 0.09),   # 限额4000 → 放量到8000需ROI>=0.09
        (8000, 0.10),   # 限额8000 → 放量到15000需ROI>=0.10
        (15000, 0.11),  # 限额15000 → 放量到更高需ROI>=0.11
    ]
    
    for row in data.get("projects", []):
        cost = row.get("cost") or 0
        roi = row.get("daily_roi") or 0
        budget = row.get("project_budget")  # 限额，可能为None
        project_name = row.get("project_name", "未知项目")
        
        # 规则1: 消耗 < 2000 → 不关注（跳过）
        if cost < 2000:
            continue
        
        # 规则2: 消耗 >= 2000 且 ROI < 0.09 → 提醒限额到4000
        if cost >= 2000 and roi < 0.09:
            if budget is None or budget == 0:
                # 未限额项目，建议设置限额4000
                messages.append(
                    f"⚠️【限额提醒】{project_name} | 消耗¥{cost:.0f} ROI={roi:.2f} | 建议设置限额到4000"
                )
            else:
                # 已有限额，但ROI不达标
                messages.append(
                    f"⚠️【关注】{project_name} | 消耗¥{cost:.0f} ROI={roi:.2f} 限额¥{budget:.0f} | ROI偏低，需关注"
                )
        
        # 规则3: 已限额账户 → 检查消耗占比和放量条件
        if budget and budget > 0:
            consumption_ratio = cost / budget
            
            # 检查是否达到80%消耗占比
            if consumption_ratio >= 0.8:
                # 查找下一档位所需的ROI
                next_roi_required = None
                for quota, required_roi in quota_tiers:
                    if budget < quota:
                        next_roi_required = required_roi
                        break
                
                if next_roi_required is None:
                    # 超过最高档位配置，默认需要0.12
                    next_roi_required = 0.12
                
                # 判断ROI是否符合放量条件
                if roi >= next_roi_required:
                    messages.append(
                        f"🔥【重点提醒】{project_name} | 消耗占比{cost}/{budget}={consumption_ratio*100:.0f}% | "
                        f"ROI={roi:.2f} >= {next_roi_required} | 符合放量条件，建议提升限额！"
                    )
                else:
                    # ROI不够，但消耗占比已高
                    messages.append(
                        f"⏳【关注】{project_name} | 消耗占比{cost}/{budget}={consumption_ratio*100:.0f}% | "
                        f"ROI={roi:.2f} < {next_roi_required} | 消耗快但ROI未达放量标准"
                    )
    
    return messages
