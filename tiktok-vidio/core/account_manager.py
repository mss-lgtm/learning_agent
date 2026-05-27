import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, asdict


@dataclass
class AccountInfo:
    account_id: str
    nickname: str
    cookie_dir: str
    created_at: str
    last_used: str
    is_active: bool = False


class AccountManager:
    """管理多个抖音账号，每个账号独立 cookie 目录"""

    ACCOUNTS_FILE = "accounts.json"

    def __init__(self, base_dir: str = ""):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(os.environ.get("APPDATA", "")) / "TikTokPublisher"
        self.cookies_base = self.base_dir / "cookies"
        self.accounts_file = self.base_dir / self.ACCOUNTS_FILE
        self.cookies_base.mkdir(parents=True, exist_ok=True)

        self._accounts: dict = {}
        self._active_account_id: Optional[str] = None
        self._load()

    def _load(self):
        if self.accounts_file.exists():
            try:
                with open(self.accounts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._active_account_id = data.get("active_account")
                for acc_data in data.get("accounts", []):
                    acc = AccountInfo(**acc_data)
                    self._accounts[acc.account_id] = acc
            except Exception:
                self._accounts = {}
                self._active_account_id = None

        self._migrate_legacy_cookies()

    def _migrate_legacy_cookies(self):
        """将旧版 cookies 目录自动迁移为默认账号"""
        if len(self._accounts) > 0:
            return

        default_cookie = self.cookies_base / "cookies.json"
        default_state = self.cookies_base / "login_state.json"

        if default_cookie.exists() or default_state.exists():
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            account = AccountInfo(
                account_id="default",
                nickname="默认账号",
                cookie_dir=str(self.cookies_base),
                created_at=now,
                last_used=now,
                is_active=True,
            )
            self._accounts["default"] = account
            self._active_account_id = "default"
            self._save()

    def _save(self):
        data = {
            "active_account": self._active_account_id,
            "accounts": [asdict(acc) for acc in self._accounts.values()],
        }
        try:
            with open(self.accounts_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_account(self, nickname: str = "") -> AccountInfo:
        account_id = f"account_{len(self._accounts) + 1}_{int(datetime.now().timestamp())}"
        if not nickname:
            nickname = f"账号 {len(self._accounts) + 1}"

        cookie_dir = str(self.cookies_base / account_id)
        Path(cookie_dir).mkdir(parents=True, exist_ok=True)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        account = AccountInfo(
            account_id=account_id,
            nickname=nickname,
            cookie_dir=cookie_dir,
            created_at=now,
            last_used=now,
            is_active=False,
        )
        self._accounts[account_id] = account
        self._save()
        return account

    def remove_account(self, account_id: str) -> bool:
        if account_id not in self._accounts:
            return False
        if self._active_account_id == account_id:
            self._active_account_id = None
        del self._accounts[account_id]
        self._save()
        return True

    def switch_account(self, account_id: str) -> Optional[AccountInfo]:
        if account_id not in self._accounts:
            return None
        for acc in self._accounts.values():
            acc.is_active = False
        self._accounts[account_id].is_active = True
        self._accounts[account_id].last_used = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._active_account_id = account_id
        self._save()
        return self._accounts[account_id]

    def get_active_account(self) -> Optional[AccountInfo]:
        if self._active_account_id and self._active_account_id in self._accounts:
            return self._accounts[self._active_account_id]
        return None

    def get_active_cookie_dir(self) -> str:
        active = self.get_active_account()
        if active:
            return active.cookie_dir
        return str(self.cookies_base)

    def list_accounts(self) -> List[AccountInfo]:
        return list(self._accounts.values())

    def update_nickname(self, account_id: str, nickname: str) -> bool:
        if account_id not in self._accounts:
            return False
        self._accounts[account_id].nickname = nickname
        self._save()
        return True
