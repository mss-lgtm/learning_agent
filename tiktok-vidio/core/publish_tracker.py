import json
import os
from pathlib import Path
from datetime import datetime


class PublishTracker:
    """记录已发布视频，防止定时任务重复发布"""

    def __init__(self, data_dir: str = ""):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(os.environ.get("APPDATA", "")) / "TikTokPublisher"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_dir / "published.json"
        self._records: dict = {}
        self._load()

    def _load(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self._records = json.load(f)
            except (json.JSONDecodeError, Exception):
                self._records = {}

    def _save(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self._records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def is_published(self, filename: str) -> bool:
        return filename in self._records

    def was_scheduled(self, filename: str) -> bool:
        record = self._records.get(filename)
        return record is not None and record.get("publish_type") == "scheduled"

    def record_publish(self, filename: str, publish_type: str = "manual"):
        self._records[filename] = {
            "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "publish_type": publish_type,
        }
        self._save()

    def get_all(self) -> dict:
        return self._records.copy()

    def clear(self):
        self._records = {}
        self._save()
