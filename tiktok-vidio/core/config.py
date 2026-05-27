import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict, field, fields
from datetime import time

# 延迟导入避免循环引用
def get_logger():
    from .logger import logger
    return logger

def get_crypto():
    from .crypto import crypto
    return crypto


@dataclass
class DouyinConfig:
    cookie_dir: str = ""


@dataclass
class ScheduleConfig:
    enabled: bool = True
    days: list = None  # ["tuesday", "thursday"]
    time: str = "17:00"

    def __post_init__(self):
        if self.days is None:
            self.days = ["tuesday", "thursday"]

    def get_time(self) -> time:
        hour, minute = map(int, self.time.split(":"))
        return time(hour, minute)


@dataclass
class AppConfig:
    video_directory: str = ""
    douyin: DouyinConfig = None
    schedule: ScheduleConfig = None
    auto_start: bool = True
    minimize_to_tray: bool = True

    def __post_init__(self):
        if self.douyin is None:
            self.douyin = DouyinConfig()
        if self.schedule is None:
            self.schedule = ScheduleConfig()


class ConfigManager:
    # 需要加密存储的字段（已移除，浏览器自动化不再需要 API 凭证）
    ENCRYPTED_FIELDS = set()

    def __init__(self):
        self.config_dir = Path(os.environ.get("APPDATA", "")) / "TikTokPublisher"
        self.config_file = self.config_dir / "config.json"
        self.config: AppConfig = AppConfig()
        self._ensure_config_dir()
        self.load()

    def _ensure_config_dir(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 过滤出 DouyinConfig 支持的字段（向后兼容旧配置）
                douyin_data = data.get("douyin", {})
                valid_fields = {f.name for f in fields(DouyinConfig)}
                filtered_douyin = {k: v for k, v in douyin_data.items() if k in valid_fields}

                self.config = AppConfig(
                    video_directory=data.get("video_directory", ""),
                    douyin=DouyinConfig(**filtered_douyin),
                    schedule=ScheduleConfig(**data.get("schedule", {})),
                    auto_start=data.get("auto_start", True),
                    minimize_to_tray=data.get("minimize_to_tray", True),
                )
            except Exception as e:
                print(f"加载配置失败: {e}")

    def save(self):
        try:
            config_dict = asdict(self.config)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def update_video_directory(self, path: str):
        old_value = self.config.video_directory
        self.config.video_directory = path
        self.save()
        get_logger().log_config_change("video_directory", old_value, path)

    def update_douyin_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config.douyin, key):
                old_value = getattr(self.config.douyin, key)
                setattr(self.config.douyin, key, value)
                # 不记录敏感信息的详细内容
                if key in self.ENCRYPTED_FIELDS:
                    get_logger().log_config_change(f"douyin.{key}", "***", "***")
                else:
                    get_logger().log_config_change(f"douyin.{key}", str(old_value)[:20], str(value)[:20])
        self.save()

    def update_schedule(self, enabled: bool = None, days: list = None, time: str = None):
        if enabled is not None:
            old_value = self.config.schedule.enabled
            self.config.schedule.enabled = enabled
            get_logger().log_config_change("schedule.enabled", str(old_value), str(enabled))
        if days is not None:
            old_value = self.config.schedule.days
            self.config.schedule.days = days
            get_logger().log_config_change("schedule.days", str(old_value), str(days))
        if time is not None:
            old_value = self.config.schedule.time
            self.config.schedule.time = time
            get_logger().log_config_change("schedule.time", old_value, time)
        self.save()

    def update_general(self, auto_start: bool = None, minimize_to_tray: bool = None):
        if auto_start is not None:
            old_value = self.config.auto_start
            self.config.auto_start = auto_start
            get_logger().log_config_change("auto_start", str(old_value), str(auto_start))
        if minimize_to_tray is not None:
            old_value = self.config.minimize_to_tray
            self.config.minimize_to_tray = minimize_to_tray
            get_logger().log_config_change("minimize_to_tray", str(old_value), str(minimize_to_tray))
        self.save()
