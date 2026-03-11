# 巨量引擎数据抓取 - 工具使用说明

## 工具列表

### 工具1：手动登录（login.py）

打开浏览器，用户手动扫码登录巨量引擎，保存登录状态供后续 headless 抓取使用。

```bash
cd /path/to/oceanengine_fetch && python login.py
```

| 退出码 | 含义 |
|--------|------|
| 0 | 登录成功，状态已保存到 `data/browser_context/auth.json` |
| 1 | 登录失败或超时（600秒） |

注意：需要有显示器的环境运行，用户在浏览器中手动扫码完成登录。

### 工具2：抓取数据（fetch_data.py）

无头浏览器访问巨量引擎，下载各组织的账户/项目/单元 Excel 数据，解析后存入 SQLite 数据库。

```bash
cd /path/to/oceanengine_fetch && python fetch_data.py --headless
```

| 退出码 | 含义 | 处理方式 |
|--------|------|----------|
| 0 | 抓取成功，数据已入库 | 可继续执行 check_rules.py |
| 2 | 登录失效（AUTH_EXPIRED） | 需要调用 `python login.py` 重新登录 |
| 1 | 其他错误 | 查看日志 `logs/fetch_data.log` 排查 |

### 工具3：检查规则（check_rules.py）

读取数据库中最新一轮抓取的数据，执行 `rules/` 目录下的规则，触发的消息通过飞书 Webhook 发送通知。

```bash
cd /path/to/oceanengine_fetch && python check_rules.py
```

| 退出码 | 含义 |
|--------|------|
| 0 | 执行成功（无论是否触发通知） |
| 1 | 执行失败 |

## 标准调用流程

```bash
cd /path/to/oceanengine_fetch && python fetch_data.py --headless && python check_rules.py
```

抓取成功后自动执行规则检查。如果抓取失败（退出码非0），不会执行规则检查。

## 环境依赖

```bash
pip install playwright openpyxl pyyaml
playwright install chromium
```

## 首次使用

1. 先运行 `python login.py` 完成手动登录
2. 之后即可用 `python fetch_data.py --headless` 无头抓取
3. 登录过期时 fetch_data.py 返回退出码 2，重新运行 login.py 即可
