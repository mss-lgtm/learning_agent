import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List


class VideoMetaManager:
    """管理视频元数据（标题、描述、标签、封面、时间），统一存储在 video_meta.json"""

    META_FILE = "video_meta.json"
    COVERS_DIR = ".covers"
    BLACK_THRESHOLD = 30  # 黑屏判定亮度阈值 (0-255)
    MAX_RETRIES = 5

    def __init__(self, video_dir: str):
        self.video_dir = Path(video_dir)
        self.meta_file = self.video_dir / self.META_FILE
        self.covers_dir = self.video_dir / self.COVERS_DIR
        self.covers_dir.mkdir(parents=True, exist_ok=True)
        self._meta: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.meta_file.exists():
            try:
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    self._meta = json.load(f)
            except (json.JSONDecodeError, Exception):
                self._meta = {}

    def _save(self):
        try:
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(self._meta, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get(self, filename: str) -> Optional[Dict[str, Any]]:
        return self._meta.get(filename)

    def get_all(self) -> Dict[str, Any]:
        return self._meta.copy()

    def set(self, filename: str, data: Dict[str, Any]):
        self._meta[filename] = data
        self._save()

    def update(self, filename: str, **fields):
        if filename not in self._meta:
            self._meta[filename] = {}
        self._meta[filename].update(fields)
        self._save()

    def update_published_at(self, filename: str):
        self.update(filename, published_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def ensure_entry(self, filename: str, default_title: str = "") -> Dict[str, Any]:
        """确保视频有配置条目，没有则用默认值创建"""
        if filename not in self._meta:
            title = default_title or Path(filename).stem
            self._meta[filename] = {
                "title": title,
                "description": "",
                "tags": [],
                "cover": "",
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "published_at": None,
            }
            self._save()
        return self._meta[filename]

    def extract_cover(self, video_path: str, filename: str) -> str:
        """从视频中智能截取封面帧，返回封面文件路径"""
        try:
            import cv2
        except ImportError:
            return ""

        cover_name = Path(filename).stem + ".jpg"
        cover_path = self.covers_dir / cover_name

        # 如果封面已存在，直接返回
        if cover_path.exists():
            return str(cover_path)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return ""

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = total_frames / fps if fps > 0 else 0

            if duration <= 0:
                return ""

            # 从 10% 位置开始，黑屏则依次尝试 20%、30%、40%、50%
            for i in range(1, self.MAX_RETRIES + 1):
                percent = i * 0.1
                if percent > 0.5:
                    break
                sec = duration * percent
                frame = self._extract_frame_at(cap, sec, fps)
                if frame is not None and not self._is_black_frame(frame):
                    self._save_frame(frame, str(cover_path))
                    return str(cover_path)

            # 兜底：取中间帧
            mid_sec = duration / 2
            frame = self._extract_frame_at(cap, mid_sec, fps)
            if frame is not None:
                self._save_frame(frame, str(cover_path))
                return str(cover_path)

            return ""
        finally:
            cap.release()

    def _extract_frame_at(self, cap, seconds: float, fps: float):
        """截取指定秒数的帧"""
        try:
            import cv2
            frame_number = int(seconds * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            return frame if ret else None
        except Exception:
            return None

    def _is_black_frame(self, frame) -> bool:
        """判断帧是否为黑屏"""
        try:
            import cv2
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mean_brightness = gray.mean()
            return mean_brightness < self.BLACK_THRESHOLD
        except Exception:
            return False

    def _save_frame(self, frame, path: str):
        """保存帧为 JPEG 图片"""
        try:
            import cv2
            cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        except Exception:
            pass

    def batch_extract_covers(self, video_files: List[Dict[str, str]]) -> int:
        """批量截取封面，返回新截取的数量"""
        count = 0
        for v in video_files:
            filename = v["filename"]
            video_path = v["path"]
            meta = self.ensure_entry(filename)
            if not meta.get("cover"):
                cover = self.extract_cover(video_path, filename)
                if cover:
                    self.update(filename, cover=cover)
                    count += 1
        return count
