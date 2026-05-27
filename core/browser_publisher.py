import json
import os
import time
import random
from pathlib import Path
from typing import Optional

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
        "user_avatar": [
            (By.CSS_SELECTOR, ".user-avatar"),
            (By.CSS_SELECTOR, "img[class*='avatar']"),
            (By.CSS_SELECTOR, "[class*='avatar']"),
        ],
    }

    def __init__(self, cookie_dir: str = ""):
        if cookie_dir:
            self.cookie_dir = Path(cookie_dir)
        else:
            self.cookie_dir = Path(os.environ.get("APPDATA", "")) / "TikTokPublisher" / "cookies"
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        self._driver: Optional[webdriver.Chrome] = None

    def _init_driver(self, headless: bool = False) -> webdriver.Chrome:
        """创建 Chrome WebDriver 实例"""
        if self._driver is not None:
            return self._driver

        chrome_options = Options()
        # 反检测措施
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        # 禁用自动化提示条
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        if headless:
            chrome_options.add_argument("--headless=new")

        try:
            service = Service(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception:
            # webdriver-manager 失败时，尝试系统自带的 ChromeDriver
            self._driver = webdriver.Chrome(options=chrome_options)

        # 隐藏 webdriver 标志
        self._driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        return self._driver

    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """随机延迟，模拟人类操作"""
        time.sleep(random.uniform(min_sec, max_sec))

    def _save_cookies(self):
        """保存 Cookie 到文件"""
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
        """从文件加载 Cookie"""
        cookie_file = self.cookie_dir / self.COOKIE_FILE_NAME
        if not cookie_file.exists():
            return False

        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)
        except (json.JSONDecodeError, Exception):
            # Cookie 文件损坏，删除
            cookie_file.unlink(missing_ok=True)
            return False

        if not cookies:
            return False

        # 先访问目标域名，才能添加 Cookie
        try:
            self._driver.get("https://creator.douyin.com")
            self._random_delay(1, 2)
        except WebDriverException:
            return False

        loaded = 0
        for cookie in cookies:
            try:
                # 移除可能导致问题的字段
                cookie.pop("sameSite", None)
                cookie.pop("expiry", None)
                self._driver.add_cookie(cookie)
                loaded += 1
            except (InvalidCookieDomainException, Exception):
                continue

        return loaded > 0

    def _check_login_status(self) -> bool:
        """检查当前页面是否已登录"""
        if not self._driver:
            return False
        try:
            current_url = self._driver.current_url
            # 如果被重定向到登录页面，说明未登录
            if "login" in current_url.lower() or "passport" in current_url.lower():
                return False
            # 检查是否在创作者平台页面
            if "creator.douyin.com" in current_url:
                return True
            return False
        except WebDriverException:
            return False

    def _wait_for_element(self, by, value, timeout=10):
        """等待元素出现"""
        return WebDriverWait(self._driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def _find_element_robust(self, selectors, timeout=10):
        """使用多个选择器尝试查找元素"""
        for by, value in selectors:
            try:
                return WebDriverWait(self._driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            except TimeoutException:
                continue
        return None

    def _find_clickable_element(self, selectors, timeout=10):
        """使用多个选择器尝试查找可点击元素"""
        for by, value in selectors:
            try:
                return WebDriverWait(self._driver, timeout).until(
                    EC.element_to_be_clickable((by, value))
                )
            except TimeoutException:
                continue
        return None

    def is_authenticated(self) -> bool:
        """检查是否已登录（通过 Cookie 文件和实际验证）"""
        cookie_file = self.cookie_dir / self.COOKIE_FILE_NAME
        if not cookie_file.exists():
            return False

        try:
            driver = self._init_driver(headless=True)
            driver.get(self.HOME_URL)
            self._random_delay(1, 2)

            if self._load_cookies():
                driver.get(self.HOME_URL)
                self._random_delay(2, 3)
                result = self._check_login_status()
                self.close()
                return result

            self.close()
            return False
        except Exception:
            self.close()
            return False

    def start_login(self) -> bool:
        """打开浏览器让用户扫码登录"""
        try:
            driver = self._init_driver(headless=False)
            driver.get(self.LOGIN_URL)
            self._random_delay(2, 3)

            # 等待用户扫码登录，最多等 120 秒
            start_time = time.time()
            timeout = 120

            while time.time() - start_time < timeout:
                try:
                    current_url = driver.current_url
                    # 登录成功后 URL 会变化
                    if "creator.douyin.com/creator-micro" in current_url:
                        self._save_cookies()
                        self._random_delay(1, 2)
                        self.close()
                        return True
                    # 检查是否有用户头像出现（登录成功标志）
                    if self._check_login_status():
                        self._save_cookies()
                        self._random_delay(1, 2)
                        self.close()
                        return True
                except WebDriverException:
                    pass

                time.sleep(2)

            # 超时
            self.close()
            return False

        except Exception as e:
            print(f"登录失败: {e}")
            self.close()
            return False

    def upload_video(self, video_path: str, title: str, description: str = "") -> dict:
        """自动上传视频到抖音"""
        # 验证文件存在
        if not Path(video_path).exists():
            return {"error": f"视频文件不存在: {video_path}"}

        try:
            driver = self._init_driver(headless=False)

            # 访问上传页面
            driver.get(self.CREATOR_URL)
            self._random_delay(2, 3)

            # 加载 Cookie
            if self._load_cookies():
                driver.get(self.CREATOR_URL)
                self._random_delay(3, 4)

            # 检查登录状态
            if not self._check_login_status():
                self.close()
                return {"error": "Cookie已过期，请重新扫码登录"}

            # 等待页面加载
            self._random_delay(2, 3)

            # 找到文件上传输入框
            try:
                file_input = self._wait_for_element(
                    By.CSS_SELECTOR, self.SELECTORS["file_input"], timeout=15
                )
            except TimeoutException:
                self.close()
                return {"error": "未找到上传入口，抖音页面可能已更新"}

            # 上传视频文件
            abs_path = os.path.abspath(video_path)
            file_input.send_keys(abs_path)

            # 等待上传完成（最多 5 分钟）
            upload_success = False
            for _ in range(60):  # 每 5 秒检查一次，共 5 分钟
                self._random_delay(4, 6)
                try:
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    for indicator in self.SELECTORS["upload_complete"]:
                        if indicator in page_text:
                            upload_success = True
                            break
                    if upload_success:
                        break
                    # 检查是否有进度条消失
                    progress_elements = driver.find_elements(
                        By.CSS_SELECTOR, "[class*='progress']"
                    )
                    if not progress_elements:
                        # 可能已经上传完成
                        upload_success = True
                        break
                except WebDriverException:
                    pass

            if not upload_success:
                self.close()
                return {"error": "视频上传超时，请检查网络连接"}

            self._random_delay(2, 3)

            # 填写标题
            if title:
                try:
                    title_element = self._find_element_robust(
                        self.SELECTORS["title_input"], timeout=10
                    )
                    if title_element:
                        title_element.clear()
                        self._random_delay(0.5, 1)
                        title_element.send_keys(title)
                except Exception:
                    pass  # 标题填写失败不影响发布

            self._random_delay(1, 2)

            # 填写描述（如果有）
            if description:
                try:
                    desc_selectors = [
                        (By.CSS_SELECTOR, "input[placeholder*='描述']"),
                        (By.CSS_SELECTOR, "input[placeholder*='description']"),
                        (By.CSS_SELECTOR, "textarea"),
                    ]
                    desc_element = self._find_element_robust(desc_selectors, timeout=5)
                    if desc_element:
                        desc_element.clear()
                        self._random_delay(0.5, 1)
                        desc_element.send_keys(description)
                except Exception:
                    pass

            self._random_delay(1, 2)

            # 点击发布按钮
            publish_btn = self._find_clickable_element(
                self.SELECTORS["publish_btn"], timeout=10
            )
            if not publish_btn:
                self.close()
                return {"error": "未找到发布按钮，抖音页面可能已更新"}

            publish_btn.click()
            self._random_delay(3, 5)

            # 等待发布成功
            try:
                # 检查是否跳转到内容管理页面或出现成功提示
                WebDriverWait(driver, 30).until(
                    lambda d: "content/manage" in d.current_url
                    or "发布成功" in d.find_element(By.TAG_NAME, "body").text
                    or "upload" not in d.current_url
                )
            except TimeoutException:
                # 可能已经在上传页面但发布成功了
                pass

            self._random_delay(1, 2)
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

    def close(self):
        """关闭浏览器"""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None
