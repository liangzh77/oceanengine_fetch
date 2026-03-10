"""数据提取模块：组织切换、表格数据抓取"""
import logging
import re
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class DataExtractor:
    def __init__(self, page: Page):
        self.page = page

    def switch_organization(self, org_name: str, app_name: str):
        """切换组织：打开组织面板，搜索app名称，点击对应节点"""
        logger.info(f"switch org: {org_name} - {app_name}")

        # 1. 点击右上角组织区域，打开面板
        org_btn = self.page.locator(".ebp-header-account-info").first
        org_btn.click()
        self.page.wait_for_timeout(2000)

        # 2. 在搜索框中输入 app 名称
        search_input = self.page.locator(
            ".ebp-team-switch-opper-container input[placeholder*='组织名称']"
        ).first
        search_input.click()
        search_input.fill(app_name)
        self.page.wait_for_timeout(2000)

        # 3. 点击搜索结果中匹配的 node-card
        #    node-card-part-content-name 包含 app 名称
        cards = self.page.locator(".node-card .node-card-part-content-name").all()
        clicked = False
        for card in cards:
            if card.is_visible() and app_name in card.inner_text():
                card.click()
                clicked = True
                break

        if not clicked:
            # fallback: 直接点包含 app_name 的文本
            self.page.get_by_text(app_name, exact=False).first.click()

        # 4. 等待页面重新加载完成
        self.page.wait_for_timeout(3000)
        try:
            self.page.wait_for_selector("table.ovui-table", timeout=30000)
            self.page.wait_for_timeout(3000)
        except Exception:
            logger.warning("table not found after org switch, waiting more...")
            self.page.wait_for_timeout(10000)
        logger.info(f"switched to: {org_name} - {app_name}")

    def _click_tab(self, tab_name: str):
        """点击指定的 tab 页（账户/项目/单元）"""
        logger.info(f"click tab: {tab_name}")
        tab = self.page.locator(f"text='{tab_name}'").first
        tab.click()
        self.page.wait_for_timeout(3000)
        try:
            self.page.wait_for_selector("table.ovui-table", timeout=15000)
            self.page.wait_for_timeout(2000)
        except Exception:
            logger.warning(f"tab '{tab_name}' table not found after click")

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
        """提取当前 ovui-table 表格数据，保留所有列（含隐藏列）以避免错位"""
        rows = []
        try:
            self.page.wait_for_selector("table.ovui-table", timeout=10000)

            # 获取第一行 thead tr 的所有 th，保留空列用占位名
            header_row = self.page.query_selector("table.ovui-table thead tr")
            if not header_row:
                logger.warning("no thead tr found")
                return rows

            header_cells = header_row.query_selector_all("th")
            headers = []
            for idx, cell in enumerate(header_cells):
                text = cell.inner_text().strip()
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if lines:
                    col_name = lines[0]
                    # 合计行的数值不作为列名，用占位
                    if re.match(r'^[\d,.%\-]+$', col_name):
                        col_name = f"_summary_{idx}"
                    headers.append(col_name)
                else:
                    headers.append(f"_col_{idx}")

            logger.info(f"headers({len(headers)}): {headers}")

            # 获取数据行
            data_rows = self.page.query_selector_all("table.ovui-table tbody tr")
            for row in data_rows:
                cells = row.query_selector_all("td")
                if not cells:
                    continue
                row_dict = {}
                for col_idx, cell in enumerate(cells):
                    if col_idx < len(headers):
                        row_dict[headers[col_idx]] = cell.inner_text().strip()
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
