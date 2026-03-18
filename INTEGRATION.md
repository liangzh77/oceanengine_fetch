# 巨量引擎数据抓取 - 工具使用说明

所有工具位于 `tools/` 目录，从项目根目录运行。

## 工具列表

### 1. 抓取数据 `tools/fetch_data.py`

无头浏览器抓取各组织的账户/项目/单元数据，按天存入数据库（同一天重复抓取自动覆盖）。网络超时自动重试3次，每次间隔5分钟。

```bash
python tools/fetch_data.py              # 抓取今天数据
python tools/fetch_data.py --day -1     # 抓取昨天数据
python tools/fetch_data.py --headless   # 无头模式
python tools/fetch_data.py --login      # 强制重新登录
```

退出码：`0` 成功 | `1` 失败 | `2` 登录过期（需运行 login.py）

stdout 输出：`SUCCESS: 2026-03-16 数据抓取完成` 或 `FAILED: 原因`

### 2. 查询数据 `tools/query_data.py`

查询数据库，输出 JSON。支持按日期、产品、账户、项目、单元过滤。

```bash
python tools/query_data.py                                    # 昨天全部数据
python tools/query_data.py --day 0                            # 今天全部数据
python tools/query_data.py --date 2026-03-15                  # 指定日期
python tools/query_data.py --day -1 --products 缘话app        # 按产品过滤
python tools/query_data.py --day -1 --table accounts          # 只看账户
python tools/query_data.py --accounts 测试                     # 按账户名模糊匹配
python tools/query_data.py --projects 春节推广                  # 按项目名模糊匹配
python tools/query_data.py --units 视频单元A                   # 按单元名模糊匹配
python tools/query_data.py --list-dates                       # 列出所有有数据的日期
```

**`--list-dates` 返回格式：**

```json
{"dates": ["2026-03-16", "2026-03-13", "2026-03-12", "2026-03-11"]}
```

**查询返回格式（按 `--table` 参数决定包含哪些表，默认 all）：**

```json
{
  "date": "2026-03-16",
  "accounts": [{ ... }, { ... }],
  "projects": [{ ... }, { ... }],
  "units": [{ ... }, { ... }]
}
```

## 数据结构

数据层级：**产品(app_name) → 账户 → 项目 → 单元**，层级之间一对多。每天每条记录唯一（UPSERT）。

### accounts 账户表

```json
{
  "org_name": "天津乾飞科技有限公司",
  "app_name": "丝话app",
  "date": "2026-03-16",
  "account_name": "伊心-丝话-安卓-每次付费-UBA-02-在投",
  "account_id": "1825413509844062",
  "account_status": "审核通过",
  "account_budget": 15000.0,
  "cost": 8876.09,
  "daily_roi": 0.11,
  "daily_pay_amount": 975.0,
  "impressions": 140978.0,
  "clicks": 2538.0,
  "conversions": 37.0,
  "avg_conversion_cost": 239.89
}
```

### projects 项目表

```json
{
  "org_name": "天津乾飞科技有限公司",
  "app_name": "丝话app",
  "date": "2026-03-16",
  "project_name": "丝话-伊心-7R-2.11-高-男",
  "project_id": "7605498720495108159",
  "status": "未投放",
  "project_budget": 3000.0,
  "cost": 502.95,
  "daily_roi": 0.1,
  "impressions": 5020.0,
  "conversions": 2.0,
  "avg_conversion_cost": 251.48
}
```

### units 单元表

```json
{
  "org_name": "天津乾飞科技有限公司",
  "app_name": "丝话app",
  "date": "2026-03-16",
  "unit_name": "丝话-伊心-7R-2.11-高-男_鲁_02_11_15:01:23_2",
  "unit_id": "7605504805607653419",
  "status": "未投放",
  "cost": 502.95,
  "daily_roi": 0.1,
  "daily_pay_amount": 49.8,
  "impressions": 5020.0,
  "clicks": 85.0,
  "conversions": 2.0,
  "avg_conversion_cost": 251.48
}
```

## 标准流程

```bash
# 首次：手动登录
python tools/login.py

# 日常：抓取数据
python tools/fetch_data.py --headless

# 登录过期时（fetch_data 退出码 2）：重新登录后再抓取
python tools/login.py && python tools/fetch_data.py --headless
```

## 环境依赖

```bash
pip install playwright openpyxl pyyaml
playwright install chromium
```
