"""浏览器管理模块：启动、登录状态保存/恢复"""
import os
import logging
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

AUTH_STATE_FILE = "auth.json"


class BrowserManager:
    def __init__(self, context_dir: str):
        self.context_dir = context_dir
        self.auth_path = os.path.join(context_dir, AUTH_STATE_FILE)
        self._playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None
        self._page: Page = None

    def _has_saved_auth(self) -> bool:
        return os.path.exists(self.auth_path)

    def start(self, headless: bool = False) -> Page:
        """启动浏览器，返回 Page 对象"""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)

        if self._has_saved_auth():
            logger.info("检测到已保存的登录状态，正在恢复...")
            self._context = self._browser.new_context(storage_state=self.auth_path, accept_downloads=True)
        else:
            logger.info("未检测到登录状态，需要人工登录")
            self._context = self._browser.new_context(accept_downloads=True)

        self._page = self._context.new_page()
        return self._page

    def save_auth(self):
        """保存当前登录状态"""
        os.makedirs(self.context_dir, exist_ok=True)
        self._context.storage_state(path=self.auth_path)
        logger.info(f"登录状态已保存到 {self.auth_path}")

    def _check_logged_in(self) -> bool:
        """检测当前页面是否已登录"""
        current_url = self._page.url
        # 不在登录页就算登录成功
        if "login" in current_url:
            return False
        return True

    def navigate_and_ensure_login(self, url: str, timeout: int = 300):
        """导航到目标页面，如果 session 失效则等待人工登录"""
        logger.info(f"正在导航到目标页面...")
        self._page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # 等待可能的重定向
        self._page.wait_for_timeout(5000)

        current_url = self._page.url
        logger.info(f"当前页面URL: {current_url}")

        if self._check_logged_in():
            logger.info("登录状态有效，已进入业务页面")
            # 更新保存的登录状态
            self.save_auth()
            return

        # session 失效，需要重新登录
        logger.warning("登录状态已失效，需要重新人工登录")
        logger.info("请在浏览器中手动登录...")
        logger.info(f"等待登录完成（最长 {timeout} 秒）...")

        import time
        start = time.time()
        while time.time() - start < timeout:
            try:
                current_url = self._page.url
                logger.debug(f"轮询检测URL: {current_url}")
                if self._check_logged_in():
                    # 再等几秒让页面内容加载
                    self._page.wait_for_timeout(5000)
                    logger.info("检测到已进入业务页面，登录成功！")
                    self.save_auth()
                    return
                self._page.wait_for_timeout(2000)
            except Exception as e:
                # 页面可能在跳转中，忽略临时错误
                logger.debug(f"轮询中遇到临时错误: {e}")
                import time as t
                t.sleep(2)

        raise TimeoutError(f"等待登录超时（{timeout}秒）")

    def close(self):
        """关闭浏览器"""
        if self._page:
            self._page.close()
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("浏览器已关闭")

    @property
    def page(self) -> Page:
        return self._page
