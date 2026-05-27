import requests
import json
import time
from typing import Optional, Dict, Any
from pathlib import Path
from .config import DouyinConfig


class DouyinAPI:
    BASE_URL = "https://open.douyin.com"
    AUTH_URL = "https://open.douyin.com/platform/oauth/access_token"
    UPLOAD_URL = "https://open.douyin.com/video/upload"
    PUBLISH_URL = "https://open.douyin.com/video/publish"

    def __init__(self, config: DouyinConfig):
        self.config = config

    def get_auth_url(self, redirect_uri: str) -> str:
        return (
            f"https://open.douyin.com/platform/oauth/connect"
            f"?client_key={self.config.client_key}"
            f"&response_type=code"
            f"&scope=user.info,video.create,video.data"
            f"&redirect_uri={redirect_uri}"
        )

    def get_access_token(self, code: str) -> Dict[str, Any]:
        data = {
            "client_key": self.config.client_key,
            "client_secret": self.config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        response = requests.post(self.AUTH_URL, data=data)
        result = response.json()

        if "data" in result and "access_token" in result["data"]:
            self.config.access_token = result["data"]["access_token"]
            self.config.refresh_token = result["data"]["refresh_token"]
            self.config.open_id = result["data"]["open_id"]
        return result

    def refresh_access_token(self) -> Dict[str, Any]:
        data = {
            "client_key": self.config.client_key,
            "grant_type": "refresh_token",
            "refresh_token": self.config.refresh_token,
        }
        response = requests.post(self.AUTH_URL, data=data)
        result = response.json()

        if "data" in result and "access_token" in result["data"]:
            self.config.access_token = result["data"]["access_token"]
            self.config.refresh_token = result["data"]["refresh_token"]
        return result

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.config.access_token}"

        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        return response.json()

    def get_user_info(self) -> Dict[str, Any]:
        return self._make_request("GET", "/oauth/userinfo/")

    def upload_video(self, video_path: str, title: str, description: str = "") -> Dict[str, Any]:
        if not self.config.access_token:
            return {"error": "未登录，请先授权"}

        video_file = Path(video_path)
        if not video_file.exists():
            return {"error": f"视频文件不存在: {video_path}"}

        # 第一步：获取上传凭证
        init_data = {
            "video_name": video_file.name,
            "video_size": video_file.stat().st_size,
        }
        init_result = self._make_request("POST", "/video/init/", json=init_data)

        if "data" not in init_result:
            return {"error": f"获取上传凭证失败: {init_result}"}

        upload_id = init_result["data"]["upload_id"]
        upload_url = init_result["data"]["upload_url"]

        # 第二步：上传视频文件
        with open(video_path, "rb") as f:
            files = {"video": (video_file.name, f, "video/mp4")}
            headers = {"Authorization": f"Bearer {self.config.access_token}"}
            upload_response = requests.post(upload_url, headers=headers, files=files)
            upload_result = upload_response.json()

        if "error" in upload_result:
            return {"error": f"上传视频失败: {upload_result}"}

        # 第三步：发布视频
        publish_data = {
            "video_id": upload_result.get("data", {}).get("video_id"),
            "text": description or title,
            "cover_tsp": 1,
        }
        publish_result = self._make_request("POST", "/video/publish/", json=publish_data)

        return publish_result

    def get_video_list(self, cursor: int = 0, count: int = 20) -> Dict[str, Any]:
        params = {
            "open_id": self.config.open_id,
            "cursor": cursor,
            "count": count,
        }
        return self._make_request("GET", "/video/list/", params=params)

    def is_authenticated(self) -> bool:
        return bool(self.config.access_token and self.config.open_id)
