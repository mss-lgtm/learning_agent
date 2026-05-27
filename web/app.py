from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import ConfigManager
from core.video_scanner import VideoScanner
from core.douyin_api import DouyinAPI
from core.scheduler import TaskScheduler
from core.logger import logger

app = Flask(__name__)
CORS(app)

config_manager = ConfigManager()
scheduler = TaskScheduler()

# 记录应用启动
logger.log_runtime("应用启动", "info")


def mask_secret(value: str) -> str:
    """对敏感信息进行脱敏"""
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify({
        "video_directory": config_manager.config.video_directory,
        "schedule": {
            "enabled": config_manager.config.schedule.enabled,
            "days": config_manager.config.schedule.days,
            "time": config_manager.config.schedule.time,
        },
        "auto_start": config_manager.config.auto_start,
        "minimize_to_tray": config_manager.config.minimize_to_tray,
    })


@app.route("/api/douyin/config", methods=["GET"])
def get_douyin_config():
    """获取抖音配置（脱敏）"""
    douyin = config_manager.config.douyin
    return jsonify({
        "client_key": douyin.client_key,
        "client_secret": mask_secret(douyin.client_secret),
        "has_client_secret": bool(douyin.client_secret),
        "is_authenticated": bool(douyin.access_token and douyin.open_id),
    })


@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.json

    if "video_directory" in data:
        config_manager.update_video_directory(data["video_directory"])

    if "schedule" in data:
        schedule_data = data["schedule"]
        config_manager.update_schedule(
            enabled=schedule_data.get("enabled"),
            days=schedule_data.get("days"),
            time=schedule_data.get("time"),
        )

    if "auto_start" in data:
        config_manager.update_general(auto_start=data["auto_start"])

    if "minimize_to_tray" in data:
        config_manager.update_general(minimize_to_tray=data["minimize_to_tray"])

    return jsonify({"success": True})


@app.route("/api/videos", methods=["GET"])
def get_videos():
    directory = config_manager.config.video_directory
    if not directory:
        return jsonify({"videos": [], "error": "未设置视频目录"})

    scanner = VideoScanner(directory)
    videos = scanner.scan()

    return jsonify({
        "videos": [
            {
                "path": v.path,
                "filename": v.filename,
                "size": v.size,
                "size_str": v.size_str,
                "modified_time": v.modified_str,
                "created_time": v.created_str,
            }
            for v in videos
        ]
    })


@app.route("/api/douyin/status", methods=["GET"])
def douyin_status():
    douyin = DouyinAPI(config_manager.config.douyin)
    return jsonify({
        "authenticated": douyin.is_authenticated(),
        "has_credentials": bool(config_manager.config.douyin.client_key),
    })


@app.route("/api/douyin/credentials", methods=["POST"])
def set_credentials():
    data = request.json

    # 准备更新的数据
    update_data = {
        "client_key": data.get("client_key", ""),
    }

    # 只有当 client_secret 不为 None 时才更新（None 表示不修改）
    client_secret = data.get("client_secret")
    if client_secret is not None:
        update_data["client_secret"] = client_secret

    config_manager.update_douyin_config(**update_data)
    logger.log_operation("保存凭证", "抖音凭证已更新（密文存储）")
    return jsonify({"success": True})


@app.route("/api/douyin/auth-url", methods=["GET"])
def get_auth_url():
    douyin = DouyinAPI(config_manager.config.douyin)
    redirect_uri = request.args.get("redirect_uri", "http://localhost:8080/callback")
    url = douyin.get_auth_url(redirect_uri)
    return jsonify({"url": url})


@app.route("/api/douyin/callback", methods=["POST"])
def douyin_callback():
    data = request.json
    code = data.get("code")
    if not code:
        return jsonify({"error": "缺少授权码"}), 400

    douyin = DouyinAPI(config_manager.config.douyin)
    result = douyin.get_access_token(code)

    if "error" in result:
        logger.log_auth("授权", "失败", result["error"])
        return jsonify({"error": result["error"]}), 400

    config_manager.update_douyin_config(
        access_token=douyin.config.access_token,
        refresh_token=douyin.config.refresh_token,
        open_id=douyin.config.open_id,
    )

    logger.log_auth("授权", "成功")
    return jsonify({"success": True})


@app.route("/api/publish", methods=["POST"])
def publish_video():
    data = request.json
    video_path = data.get("video_path")
    title = data.get("title", "")
    description = data.get("description", "")

    if not video_path:
        return jsonify({"error": "未指定视频路径"}), 400

    douyin = DouyinAPI(config_manager.config.douyin)
    if not douyin.is_authenticated():
        logger.log_publish(title, "失败", "未授权")
        return jsonify({"error": "未授权，请先登录抖音"}), 400

    from pathlib import Path
    video_name = Path(video_path).name

    result = douyin.upload_video(video_path, title, description)

    if "error" in result:
        logger.log_publish(video_name, "失败", result["error"])
        return jsonify({"error": result["error"]}), 400

    logger.log_publish(video_name, "成功")
    return jsonify({"success": True, "result": result})


@app.route("/api/scheduler/status", methods=["GET"])
def scheduler_status():
    status = scheduler.get_status()
    return jsonify(status)


@app.route("/api/scheduler/start", methods=["POST"])
def start_scheduler():
    def publish_callback():
        directory = config_manager.config.video_directory
        if not directory:
            logger.log_scheduler("执行", "未设置视频目录")
            return

        scanner = VideoScanner(directory)
        video = scanner.get_latest_video()
        if video:
            douyin = DouyinAPI(config_manager.config.douyin)
            if douyin.is_authenticated():
                logger.log_scheduler("执行", f"发布视频: {video.filename}")
                result = douyin.upload_video(video.path, video.filename, "")
                if "error" in result:
                    logger.log_publish(video.filename, "失败", result["error"])
                else:
                    logger.log_publish(video.filename, "成功")
            else:
                logger.log_scheduler("执行", "未授权，跳过发布")

    scheduler.set_callback(publish_callback)
    scheduler.update_schedule(config_manager.config.schedule)
    scheduler.start()

    logger.log_scheduler("启动")
    return jsonify({"success": True})


@app.route("/api/scheduler/stop", methods=["POST"])
def stop_scheduler():
    scheduler.stop()
    logger.log_scheduler("停止")
    return jsonify({"success": True})


# ==================== 日志管理API ====================

@app.route("/api/logs/runtime", methods=["GET"])
def get_runtime_logs():
    lines = request.args.get("lines", 100, type=int)
    level = request.args.get("level", None)
    logs = logger.get_runtime_logs(lines, level)
    return jsonify({"logs": logs})


@app.route("/api/logs/operations", methods=["GET"])
def get_operation_logs():
    limit = request.args.get("limit", 100, type=int)
    action = request.args.get("action", None)
    logs = logger.get_operation_logs(limit, action)
    return jsonify({"logs": logs})


@app.route("/api/logs/errors", methods=["GET"])
def get_error_logs():
    lines = request.args.get("lines", 50, type=int)
    logs = logger.get_error_logs(lines)
    return jsonify({"logs": logs})


@app.route("/api/logs/stats", methods=["GET"])
def get_log_stats():
    stats = logger.get_log_stats()
    return jsonify(stats)


@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    data = request.json
    log_type = data.get("type", "all")
    logger.clear_logs(log_type)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
