import json
import os
import time
import random
from pathlib import Path
from typing import Optional
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    InvalidCookieDomainException,
)
from webdriver_manager.chrome import ChromeDriverManager


class BrowserPublisher:
    """通过 Selenium 自动化抖音创作者平台发布视频，无需开放平台 API 认证"""

    CREATOR_URL = "https://creator.douyin.com/creator-micro/content/upload"
    HOME_URL = "https://creator.douyin.com/creator-micro/home"
    LOGIN_URL = "https://creator.douyin.com"
    COOKIE_FILE_NAME = "cookies.json"
    STATE_FILE_NAME = "login_state.json"

    # 页面元素选择器集中管理，方便抖音改版后统一修改
    SELECTORS = {
        "file_input": "input[type='file']",
        "upload_complete": [
            "上传完成",
            "重新上传",
            "Upload complete",
        ],
        "title_input": [
            (By.CSS_SELECTOR, "input[placeholder*='标题']"),
            (By.CSS_SELECTOR, "input[placeholder*='title']"),
            (By.CSS_SELECTOR, "[contenteditable='true']"),
            (By.CSS_SELECTOR, ".title-input input"),
            (By.CSS_SELECTOR, ".video-title input"),
        ],
        "publish_btn": [
            (By.XPATH, "//button[contains(text(),'发布')]"),
            (By.XPATH, "//button[contains(text(),'Publish')]"),
            (By.CSS_SELECTOR, "button.publish-btn"),
            (By.CSS_SELECTOR, "button[class*='publish']"),
        ],
    }

    def __init__(self, cookie_dir: str = ""):
        if cookie_dir:
            self.cookie_dir = Path(cookie_dir)
        else:
            self.cookie_dir = Path(os.environ.get("APPDATA", "")) / "TikTokPublisher" / "cookies"
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        self._driver: Optional[webdriver.Chrome] = None

    # ==================== 登录状态管理（快速，不启动浏览器） ====================

    def _get_state_file(self) -> Path:
        return self.cookie_dir / self.STATE_FILE_NAME

    def _save_login_state(self, logged_in: bool):
        """保存登录状态到文件"""
        state = {
            "logged_in": logged_in,
            "time": datetime.now().isoformat(),
        }
        try:
            with open(self._get_state_file(), "w", encoding="utf-8") as f:
                json.dump(state, f)
        except Exception:
            pass

    def _load_login_state(self) -> bool:
        """从文件读取登录状态（快速，不启动浏览器）"""
        state_file = self._get_state_file()
        cookie_file = self.cookie_dir / self.COOKIE_FILE_NAME

        # 必须两个文件都存在才算已登录
        if not state_file.exists() or not cookie_file.exists():
            return False

        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            return state.get("logged_in", False)
        except Exception:
            return False

    def is_authenticated(self) -> bool:
        """检查是否已登录（快速检查，不启动浏览器）"""
        return self._load_login_state()

    # ==================== 浏览器驱动管理 ====================

    def _init_driver(self, headless: bool = False) -> webdriver.Chrome:
        """创建 Chrome WebDriver 实例"""
        if self._driver is not None:
            return self._driver

        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        if headless:
            chrome_options.add_argument("--headless=new")

        try:
            service = Service(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception:
            self._driver = webdriver.Chrome(options=chrome_options)

        self._driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return self._driver

    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        time.sleep(random.uniform(min_sec, max_sec))

    def close(self):
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

    # ==================== Cookie 管理 ====================

    def _save_cookies(self):
        if not self._driver:
            return
        try:
            cookies = self._driver.get_cookies()
            cookie_file = self.cookie_dir / self.COOKIE_FILE_NAME
            with open(cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存 Cookie 失败: {e}")

    def _load_cookies(self) -> bool:
        cookie_file = self.cookie_dir / self.COOKIE_FILE_NAME
        if not cookie_file.exists():
            return False

        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)
        except (json.JSONDecodeError, Exception):
            cookie_file.unlink(missing_ok=True)
            return False

        if not cookies:
            return False

        try:
            self._driver.get("https://creator.douyin.com")
            time.sleep(1)
        except WebDriverException:
            return False

        loaded = 0
        for cookie in cookies:
            try:
                cookie.pop("sameSite", None)
                cookie.pop("expiry", None)
                self._driver.add_cookie(cookie)
                loaded += 1
            except (InvalidCookieDomainException, Exception):
                continue

        return loaded > 0

    def _check_page_login(self) -> bool:
        """检查当前页面是否已登录（需要在已加载的页面上调用）"""
        if not self._driver:
            return False
        try:
            current_url = self._driver.current_url
            if "login" in current_url.lower() or "passport" in current_url.lower():
                return False
            if "creator.douyin.com" in current_url:
                return True
            return False
        except WebDriverException:
            return False

    # ==================== 元素查找辅助 ====================

    def _find_element_robust(self, selectors, timeout=10):
        for by, value in selectors:
            try:
                return WebDriverWait(self._driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            except TimeoutException:
                continue
        return None

    def _find_clickable_element(self, selectors, timeout=10):
        for by, value in selectors:
            try:
                return WebDriverWait(self._driver, timeout).until(
                    EC.element_to_be_clickable((by, value))
                )
            except TimeoutException:
                continue
        return None

    # ==================== 用户名抓取 ====================

    def scrape_username(self) -> str:
        """登录成功后从创作者平台页面抓取用户名，失败返回空字符串"""
        if not self._driver:
            return ""
        try:
            # 多种选择器尝试获取用户名
            selectors = [
                (By.CSS_SELECTOR, ".user-name"),
                (By.CSS_SELECTOR, "[class*='userName']"),
                (By.CSS_SELECTOR, "[class*='user-name']"),
                (By.CSS_SELECTOR, "[class*='nickname']"),
                (By.XPATH, "//span[contains(@class,'name')]"),
                (By.CSS_SELECTOR, ".avatar-name"),
                (By.CSS_SELECTOR, "[class*='Avatar'] + span"),
                (By.CSS_SELECTOR, "[class*='avatar'] + *"),
            ]
            for by, value in selectors:
                try:
                    el = WebDriverWait(self._driver, 5).until(
                        EC.presence_of_element_located((by, value))
                    )
                    text = el.text.strip()
                    if text and len(text) < 50:
                        return text
                except (TimeoutException, WebDriverException):
                    continue

            # 最后尝试从页面 body 文本中提取（备选）
            return ""
        except Exception:
            return ""

    # ==================== 扫码登录 ====================

    def start_login(self) -> bool:
        """打开浏览器让用户扫码登录"""
        try:
            driver = self._init_driver(headless=False)
            driver.get(self.LOGIN_URL)

            # 等待页面加载
            time.sleep(3)

            # 等待用户扫码，最多 120 秒
            start_time = time.time()
            timeout = 120

            while time.time() - start_time < timeout:
                try:
                    current_url = driver.current_url
                    # 登录成功后 URL 会包含 creator-micro
                    if "creator.douyin.com/creator-micro" in current_url:
                        self._save_cookies()
                        self._save_login_state(True)
                        time.sleep(1)
                        self.close()
                        return True
                except WebDriverException:
                    pass
                time.sleep(2)

            # 超时
            self._save_login_state(False)
            self.close()
            return False

        except Exception as e:
            print(f"登录失败: {e}")
            self._save_login_state(False)
            self.close()
            return False

    def start_login_and_get_username(self) -> tuple:
        """扫码登录并抓取用户名。返回 (success: bool, username: str)"""
        try:
            driver = self._init_driver(headless=False)
            driver.get(self.LOGIN_URL)
            time.sleep(3)

            start_time = time.time()
            timeout = 120

            while time.time() - start_time < timeout:
                try:
                    current_url = driver.current_url
                    if "creator.douyin.com/creator-micro" in current_url:
                        self._save_cookies()
                        self._save_login_state(True)
                        time.sleep(2)
                        # 抓取用户名
                        username = self.scrape_username()
                        self.close()
                        return True, username
                except WebDriverException:
                    pass
                time.sleep(2)

            self._save_login_state(False)
            self.close()
            return False, ""

        except Exception as e:
            print(f"登录失败: {e}")
            self._save_login_state(False)
            self.close()
            return False, ""

    # ==================== 视频上传 ====================

    def upload_video(self, video_path: str, title: str, description: str = "") -> dict:
        """自动上传视频到抖音"""
        if not Path(video_path).exists():
            return {"error": f"视频文件不存在: {video_path}"}

        # 检查是否有 cookie 文件
        cookie_file = self.cookie_dir / self.COOKIE_FILE_NAME
        if not cookie_file.exists():
            return {"error": "未登录，请先扫码登录"}

        try:
            driver = self._init_driver(headless=False)

            # 先访问域名再加载 cookie
            driver.get("https://creator.douyin.com")
            time.sleep(2)

            # 加载 Cookie
            if not self._load_cookies():
                self._save_login_state(False)
                self.close()
                return {"error": "Cookie加载失败，请重新扫码登录"}

            # 访问上传页面
            driver.get(self.CREATOR_URL)
            time.sleep(3)

            # 检查登录状态
            if not self._check_page_login():
                self._save_login_state(False)
                self.close()
                return {"error": "Cookie已过期，请重新扫码登录"}

            # 找到文件上传输入框
            try:
                file_input = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
            except TimeoutException:
                self.close()
                return {"error": "未找到上传入口，抖音页面可能已更新"}

            # 上传视频文件
            abs_path = os.path.abspath(video_path)
            file_input.send_keys(abs_path)

            # 等待上传完成（最多 5 分钟）
            upload_success = False
            for _ in range(60):
                time.sleep(5)
                try:
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    for indicator in self.SELECTORS["upload_complete"]:
                        if indicator in page_text:
                            upload_success = True
                            break
                    if upload_success:
                        break
                except WebDriverException:
                    pass

            if not upload_success:
                self.close()
                return {"error": "视频上传超时，请检查网络连接"}

            time.sleep(2)

            # 填写标题
            if title:
                try:
                    title_el = self._find_element_robust(self.SELECTORS["title_input"], 10)
                    if title_el:
                        title_el.clear()
                        time.sleep(0.5)
                        title_el.send_keys(title)
                except Exception:
                    pass

            time.sleep(1)

            # 填写描述
            if description:
                try:
                    desc_selectors = [
                        (By.CSS_SELECTOR, "input[placeholder*='描述']"),
                        (By.CSS_SELECTOR, "textarea"),
                    ]
                    desc_el = self._find_element_robust(desc_selectors, 5)
                    if desc_el:
                        desc_el.clear()
                        time.sleep(0.5)
                        desc_el.send_keys(description)
                except Exception:
                    pass

            time.sleep(1)

            # 点击发布按钮
            publish_btn = self._find_clickable_element(self.SELECTORS["publish_btn"], 10)
            if not publish_btn:
                self.close()
                return {"error": "未找到发布按钮，抖音页面可能已更新"}

            publish_btn.click()
            time.sleep(5)

            # 检查是否发布成功
            try:
                WebDriverWait(driver, 30).until(
                    lambda d: "upload" not in d.current_url
                    or "发布成功" in d.find_element(By.TAG_NAME, "body").text
                )
            except TimeoutException:
                pass

            self.close()
            return {"success": True}

        except TimeoutException:
            self.close()
            return {"error": "操作超时，请检查网络连接"}
        except NoSuchElementException:
            self.close()
            return {"error": "页面元素未找到，抖音页面可能已更新"}
        except WebDriverException as e:
            self.close()
            return {"error": f"浏览器错误: {str(e)[:100]}"}
        except Exception as e:
            self.close()
            return {"error": f"发布失败: {str(e)[:100]}"}
