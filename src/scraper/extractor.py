"""数据提取模块：组织切换、表格数据抓取"""
import logging
import re
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class DataExtractor:
    def __init__(self, page: Page):
        self.page = page

    def switch_organization(self, org_name: str, app_name: str):
        """切换组织：点击右上角组织信息区域"""
        logger.info(f"switch org: {org_name} - {app_name}")
        org_btn = self.page.locator(".ebp-header-account-info").first
        org_btn.click()
        self.page.wait_for_timeout(2000)
        self.page.get_by_text(org_name, exact=False).first.click()
        self.page.wait_for_timeout(1000)
        self.page.get_by_text(app_name, exact=False).first.click()
        self.page.wait_for_timeout(5000)
        logger.info(f"switched to: {org_name} - {app_name}")

    def _click_tab(self, tab_name: str):
        """点击指定的 tab 页（账户/项目/单元）"""
        logger.info(f"click tab: {tab_name}")
        tab = self.page.locator(f"text='{tab_name}'").first
        tab.click()
        self.page.wait_for_timeout(3000)
        try:
            self.page.wait_for_selector("table.ovui-table tbody tr", timeout=10000)
        except Exception:
            logger.warning(f"tab '{tab_name}' table rows not found after click")

    def _get_total_count(self) -> int:
        """从合计行获取总条数，如 '合计（22项）' -> 22"""
        try:
            # 找表头中包含"合计"的单元格
            header_cells = self.page.query_selector_all("table.ovui-table thead th")
            for cell in header_cells:
                text = cell.inner_text().strip()
                match = re.search(r'合计[（(](\d+)项[）)]', text)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        return 0

    def _extract_table_data(self) -> list[dict]:
        """提取当前 ovui-table 表格数据，处理表头中混入合计数据的问题"""
        rows = []
        try:
            self.page.wait_for_selector("table.ovui-table", timeout=10000)

            # 获取表头 - 只取真正的列名，过滤掉合计数据
            headers = []
            header_cells = self.page.query_selector_all("table.ovui-table thead th")
            for cell in header_cells:
                text = cell.inner_text().strip()
                # 表头文本可能是多行的，取第一行作为列名
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if lines:
                    col_name = lines[0]
                    # 跳过合计行的数据（如 "合计（5项）"后面的数字）
                    if re.match(r'^[\d,.%\-]+$', col_name):
                        continue
                    headers.append(col_name)

            logger.info(f"headers({len(headers)}): {headers}")

            # 获取数据行
            data_rows = self.page.query_selector_all("table.ovui-table tbody tr")
            for row in data_rows:
                cells = row.query_selector_all("td")
                if not cells:
                    continue
                row_dict = {}
                col_idx = 0
                for cell in cells:
                    text = cell.inner_text().strip()
                    if col_idx < len(headers):
                        row_dict[headers[col_idx]] = text
                    col_idx += 1
                if row_dict and any(v for v in row_dict.values()):
                    rows.append(row_dict)

            logger.info(f"extracted {len(rows)} rows")
        except Exception as e:
            logger.error(f"extract table failed: {e}")
        return rows

    def _extract_all_pages(self) -> list[dict]:
        """提取所有分页的数据，通过总条数控制翻页"""
        total = self._get_total_count()
        logger.info(f"total count from header: {total}")

        all_rows = []
        page_num = 1
        max_pages = max((total // 5) + 2, 3) if total > 0 else 1  # 安全上限

        while page_num <= max_pages:
            logger.info(f"extracting page {page_num}/{max_pages}...")
            rows = self._extract_table_data()
            all_rows.extend(rows)

            # 已经拿够了
            if total > 0 and len(all_rows) >= total:
                break

            # 尝试点下一页
            try:
                next_btn = self.page.locator(
                    "[class*='pagination'] [class*='next']"
                ).first
                if not next_btn.is_visible():
                    break
                # 检查是否 disabled
                cls = next_btn.get_attribute("class") or ""
                if "disabled" in cls:
                    break
                next_btn.click()
                self.page.wait_for_timeout(3000)
                page_num += 1
            except Exception:
                break

        logger.info(f"total: {len(all_rows)} rows from {page_num} pages")
        return all_rows

    def fetch_accounts(self) -> list[dict]:
        self._click_tab("账户")
        return self._extract_all_pages()

    def fetch_projects(self) -> list[dict]:
        self._click_tab("项目")
        return self._extract_all_pages()

    def fetch_units(self) -> list[dict]:
        self._click_tab("单元")
        return self._extract_all_pages()

    def fetch_all(self) -> dict:
        return {
            "accounts": self.fetch_accounts(),
            "projects": self.fetch_projects(),
            "units": self.fetch_units(),
        }
