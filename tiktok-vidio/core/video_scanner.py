import os
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional
import mimetypes


@dataclass
class VideoFile:
    path: str
    filename: str
    size: int
    modified_time: datetime
    created_time: datetime
    duration: Optional[float] = None  # 秒

    @property
    def size_str(self) -> str:
        size = self.size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def modified_str(self) -> str:
        return self.modified_time.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def created_str(self) -> str:
        return self.created_time.strftime("%Y-%m-%d %H:%M:%S")


VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".3gp", ".ts"
}


class VideoScanner:
    def __init__(self, directory: str):
        self.directory = Path(directory)

    def scan(self, recursive: bool = False) -> List[VideoFile]:
        if not self.directory.exists():
            return []

        videos = []
        pattern = "**/*" if recursive else "*"

        for file_path in self.directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
                try:
                    stat = file_path.stat()
                    video = VideoFile(
                        path=str(file_path),
                        filename=file_path.name,
                        size=stat.st_size,
                        modified_time=datetime.fromtimestamp(stat.st_mtime),
                        created_time=datetime.fromtimestamp(stat.st_ctime),
                    )
                    videos.append(video)
                except Exception as e:
                    print(f"读取文件信息失败 {file_path}: {e}")

        return sorted(videos, key=lambda v: v.modified_time, reverse=True)

    def get_latest_video(self) -> Optional[VideoFile]:
        videos = self.scan()
        return videos[0] if videos else None

    def get_videos_since(self, since: datetime) -> List[VideoFile]:
        videos = self.scan()
        return [v for v in videos if v.modified_time >= since]

    def get_newest_by_week(self) -> Optional[VideoFile]:
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        videos = self.scan()
        for video in videos:
            if video.modified_time >= week_start:
                return video
        return None
