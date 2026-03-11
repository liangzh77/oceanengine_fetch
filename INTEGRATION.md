# 巨量引擎数据抓取 - OpenClaw 集成说明

## 概述

本项目提供三个 Python 工具：

| 工具 | 命令 | 功能 |
|------|------|------|
| 手动登录 | `python login.py` | 打开浏览器，用户手动登录，保存登录状态 |
| 抓取数据 | `python fetch_data.py --headless` | 无头浏览器下载 Excel，解析入库 |
| 检查规则 | `python check_rules.py` | 读取最新数据，执行规则，触发飞书通知 |

### fetch_data.py 退出码

| 退出码 | 含义 | 处理方式 |
|--------|------|----------|
| 0 | 成功 | 继续执行 check_rules.py |
| 2 | 登录失效（AUTH_EXPIRED） | 需要调用 `python login.py` 重新登录 |
| 1 | 其他错误 | 查看日志 `logs/fetch_data.log` 排查 |

## 需要拷贝的文件

将整个 `oceanengine_fetch` 项目目录拷贝到 OpenClaw 服务器上，保持目录结构：

```
oceanengine_fetch/
├── config/config.yaml          # 配置（组织列表、飞书webhook、数据库路径）
├── login.py                    # 工具1：手动登录
├── fetch_data.py               # 工具2：抓取数据
├── check_rules.py              # 工具3：检查规则
├── rules/                      # 规则目录（可自定义规则文件）
│   └── example_roi_alert.py
├── src/
│   ├── scraper/                # 浏览器操作 + Excel解析
│   │   ├── browser.py
│   │   ├── extractor.py
│   │   └── parser.py
│   ├── database/
│   │   └── db_manager.py       # SQLite 时间序列数据库
│   ├── rules/
│   │   └── rule_engine.py      # 规则引擎
│   └── notification/
│       └── feishu.py           # 飞书通知
├── data/                       # 运行时数据（自动创建）
│   ├── browser_context/        # 浏览器登录状态
│   └── oceanengine.db          # SQLite 数据库
└── logs/                       # 日志目录
```

## 环境依赖

在 OpenClaw 服务器上安装：

```bash
pip install playwright openpyxl pyyaml
playwright install chromium
```

## OpenClaw 集成方式

### 方式一：通过 Cron 定时任务（推荐）

OpenClaw 支持通过 `openclaw cron add` 添加定时任务。只需配置一个 cron job，抓取完数据后自动执行规则检查：

```bash
openclaw cron add \
  --name "oceanengine-fetch" \
  --schedule "*/30 9-22 * * *" \
  --message "执行巨量引擎数据抓取和规则检查：cd /path/to/oceanengine_fetch && python fetch_data.py --headless && python check_rules.py"
```

将 `/path/to/oceanengine_fetch` 替换为实际路径。

`fetch_data.py` 成功完成后会自动执行 `check_rules.py`，如果抓取失败则不会执行规则检查（`&&` 短路）。

### 方式二：通过 Skill 集成

在 OpenClaw 的 `skills/` 目录下创建 `oceanengine/SKILL.md`：

```markdown
---
name: oceanengine
description: 巨量引擎广告数据抓取和规则检查。用于抓取广告账户/项目/单元数据，检查规则并发送飞书通知。
---

# 巨量引擎数据工具

## 可用命令

### 手动登录（登录失效时使用）
打开浏览器让用户手动登录，保存登录状态：
\`\`\`bash
cd /path/to/oceanengine_fetch && python login.py
\`\`\`

### 抓取数据并检查规则（标准流程）
执行以下命令抓取最新广告数据并自动检查规则：
\`\`\`bash
cd /path/to/oceanengine_fetch && python fetch_data.py --headless && python check_rules.py
\`\`\`
如果返回退出码 2，表示登录失效，需要先执行手动登录。

### 仅抓取数据
\`\`\`bash
cd /path/to/oceanengine_fetch && python fetch_data.py --headless
\`\`\`

### 仅检查规则
\`\`\`bash
cd /path/to/oceanengine_fetch && python check_rules.py
\`\`\`

### 查看数据库
查看当前数据库中的数据统计：
\`\`\`bash
cd /path/to/oceanengine_fetch && sqlite3 data/oceanengine.db "SELECT 'accounts: ' || COUNT(*) FROM accounts; SELECT 'projects: ' || COUNT(*) FROM projects; SELECT 'units: ' || COUNT(*) FROM units;"
\`\`\`

## 注意事项
- login.py 需要有显示器的环境，用户手动扫码登录
- fetch_data.py --headless 无头运行，登录失效时退出码为 2
- check_rules.py 纯数据库操作，不需要浏览器
- 标准流程是先抓取再检查规则，抓取成功后自动��行规则检查
```

## 典型调度策略

每天 9:00-22:00，每 30 分钟执行一次抓取 + 规则检查：

```
cron 表达式：*/30 9-22 * * *
命令：cd /path/to/oceanengine_fetch && python fetch_data.py && python check_rules.py
```

## 首次部署注意

1. 首次运行 `python login.py` 手动登录巨量引擎（扫码），登录状态会保存到 `data/browser_context/auth.json`
2. 之后 `python fetch_data.py --headless` 会自动复用登录状态
3. 如果登录过期，`fetch_data.py` 会返回退出码 2（AUTH_EXPIRED），此时需要重新运行 `python login.py`
4. 如果在无头服务器上运行，需要先在有显示器的环境运行 `login.py` 完成登录，再把 `data/browser_context/` 拷贝过去
