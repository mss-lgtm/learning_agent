import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import json


class LogManager:
    """日志管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 日志目录
        self.log_dir = Path(os.environ.get("APPDATA", "")) / "TikTokPublisher" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 日志文件
        self.runtime_log = self.log_dir / "runtime.log"
        self.operation_log = self.log_dir / "operations.log"
        self.error_log = self.log_dir / "errors.log"

        # 配置日志记录器
        self._setup_loggers()

        # 操作日志列表（内存缓存）
        self._operations = []
        self._load_operations()

    def _setup_loggers(self):
        """配置日志记录器"""

        # 运行时日志
        self.runtime_logger = logging.getLogger("runtime")
        self.runtime_logger.setLevel(logging.DEBUG)

        runtime_handler = logging.FileHandler(
            self.runtime_log, encoding="utf-8"
        )
        runtime_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        self.runtime_logger.addHandler(runtime_handler)

        # 错误日志
        self.error_logger = logging.getLogger("error")
        self.error_logger.setLevel(logging.ERROR)

        error_handler = logging.FileHandler(
            self.error_log, encoding="utf-8"
        )
        error_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        self.error_logger.addHandler(error_handler)

    def _load_operations(self):
        """加载操作日志"""
        if self.operation_log.exists():
            try:
                with open(self.operation_log, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self._operations.append(json.loads(line))
            except Exception:
                pass

    def _save_operation(self, operation: dict):
        """保存操作日志到文件"""
        self._operations.append(operation)

        # 保留最近1000条
        if len(self._operations) > 1000:
            self._operations = self._operations[-1000:]

        try:
            with open(self.operation_log, "w", encoding="utf-8") as f:
                for op in self._operations:
                    f.write(json.dumps(op, ensure_ascii=False) + "\n")
        except Exception as e:
            self.runtime_logger.error(f"保存操作日志失败: {e}")

    def log_runtime(self, message: str, level: str = "info"):
        """记录运行时日志"""
        level = level.lower()
        if level == "debug":
            self.runtime_logger.debug(message)
        elif level == "info":
            self.runtime_logger.info(message)
        elif level == "warning":
            self.runtime_logger.warning(message)
        elif level == "error":
            self.runtime_logger.error(message)
            self.error_logger.error(message)
        elif level == "critical":
            self.runtime_logger.critical(message)
            self.error_logger.critical(message)

    def log_operation(self, action: str, details: str = "", status: str = "success"):
        """记录操作日志"""
        operation = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details,
            "status": status,
        }
        self._save_operation(operation)
        self.runtime_logger.info(f"操作: {action} - {details} [{status}]")

    def log_publish(self, video_name: str, status: str, message: str = ""):
        """记录发布日志"""
        details = f"视频: {video_name}"
        if message:
            details += f" - {message}"
        self.log_operation("发布视频", details, status)

    def log_config_change(self, key: str, old_value: str, new_value: str):
        """记录配置变更"""
        details = f"{key}: {old_value} -> {new_value}"
        self.log_operation("修改配置", details)

    def log_auth(self, action: str, status: str, message: str = ""):
        """记录认证日志"""
        self.log_operation(f"认证-{action}", message, status)

    def log_scheduler(self, action: str, message: str = ""):
        """记录调度器日志"""
        self.log_operation(f"调度器-{action}", message)
        self.runtime_logger.info(f"调度器: {action} - {message}")

    def get_runtime_logs(self, lines: int = 100, level: str = None) -> list:
        """获取运行时日志"""
        if not self.runtime_log.exists():
            return []

        try:
            with open(self.runtime_log, "r", encoding="utf-8") as f:
                all_lines = f.readlines()

            # 过滤级别
            if level:
                level = level.upper()
                all_lines = [l for l in all_lines if f"[{level}]" in l]

            # 返回最后N行
            recent_lines = all_lines[-lines:]
            return [
                {
                    "timestamp": line[:19] if len(line) > 19 else "",
                    "level": self._extract_level(line),
                    "message": line[20:].strip() if len(line) > 20 else line.strip(),
                }
                for line in recent_lines
            ]
        except Exception:
            return []

    def get_operation_logs(self, limit: int = 100, action: str = None) -> list:
        """获取操作日志"""
        logs = self._operations.copy()

        # 过滤操作类型
        if action:
            logs = [op for op in logs if op.get("action") == action]

        # 返回最后N条
        return logs[-limit:]

    def get_error_logs(self, lines: int = 50) -> list:
        """获取错误日志"""
        if not self.error_log.exists():
            return []

        try:
            with open(self.error_log, "r", encoding="utf-8") as f:
                all_lines = f.readlines()

            recent_lines = all_lines[-lines:]
            return [
                {
                    "timestamp": line[:19] if len(line) > 19 else "",
                    "message": line[20:].strip() if len(line) > 20 else line.strip(),
                }
                for line in recent_lines
            ]
        except Exception:
            return []

    def _extract_level(self, line: str) -> str:
        """从日志行提取级别"""
        if "[DEBUG]" in line:
            return "DEBUG"
        elif "[INFO]" in line:
            return "INFO"
        elif "[WARNING]" in line:
            return "WARNING"
        elif "[ERROR]" in line:
            return "ERROR"
        elif "[CRITICAL]" in line:
            return "CRITICAL"
        return "INFO"

    def clear_logs(self, log_type: str = "all"):
        """清除日志"""
        if log_type in ("all", "runtime"):
            if self.runtime_log.exists():
                self.runtime_log.write_text("", encoding="utf-8")

        if log_type in ("all", "operation"):
            self._operations = []
            if self.operation_log.exists():
                self.operation_log.write_text("", encoding="utf-8")

        if log_type in ("all", "error"):
            if self.error_log.exists():
                self.error_log.write_text("", encoding="utf-8")

        self.log_operation("清除日志", f"类型: {log_type}")

    def get_log_stats(self) -> dict:
        """获取日志统计"""
        runtime_lines = 0
        error_lines = 0

        if self.runtime_log.exists():
            try:
                with open(self.runtime_log, "r", encoding="utf-8") as f:
                    runtime_lines = sum(1 for _ in f)
            except:
                pass

        if self.error_log.exists():
            try:
                with open(self.error_log, "r", encoding="utf-8") as f:
                    error_lines = sum(1 for _ in f)
            except:
                pass

        return {
            "runtime_lines": runtime_lines,
            "operation_count": len(self._operations),
            "error_lines": error_lines,
            "log_dir": str(self.log_dir),
        }


# 全局日志管理器实例
logger = LogManager()
