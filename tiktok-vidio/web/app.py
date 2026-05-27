from flask import Flask, render_template, jsonify, request, send_file, Response
from flask_cors import CORS
import sys
import os
import re
import threading
from pathlib import Path
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import ConfigManager
from core.video_scanner import VideoScanner
from core.browser_publisher import BrowserPublisher
from core.scheduler import TaskScheduler
from core.publish_tracker import PublishTracker
from core.account_manager import AccountManager
from core.logger import logger

app = Flask(__name__)
CORS(app)

config_manager = ConfigManager()
scheduler = TaskScheduler()
publish_tracker = PublishTracker()
account_manager = AccountManager()
browser_publisher = BrowserPublisher(cookie_dir=account_manager.get_active_cookie_dir())

# 登录状态跟踪
_login_in_progress = False
_login_result = None

# 创建并登录状态跟踪
_create_login_in_progress = False
_create_login_result = None
_create_login_account = None

# 记录应用启动
logger.log_runtime("应用启动", "info")


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
    """获取抖音配置"""
    cookie_file = browser_publisher.cookie_dir / BrowserPublisher.COOKIE_FILE_NAME
    return jsonify({
        "has_cookies": cookie_file.exists(),
        "cookie_dir": str(browser_publisher.cookie_dir),
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
                "path": v.path.replace("\\", "/"),
                "filename": v.filename,
                "size": v.size,
                "size_str": v.size_str,
                "modified_time": v.modified_str,
                "created_time": v.created_str,
            }
            for v in videos
        ]
    })


@app.route("/api/video/preview", methods=["GET"])
def video_preview():
    video_path = request.args.get("path", "").replace("\\", "/")
    if not video_path:
        return jsonify({"error": "未指定视频路径"}), 400

    file_path = Path(video_path)
    if not file_path.exists():
        return jsonify({"error": "视频文件不存在"}), 404

    import mimetypes
    mime_type = mimetypes.guess_type(str(file_path))[0] or "video/mp4"
    file_size = file_path.stat().st_size

    # 处理 Range 请求（视频拖拽/seek 必需）
    range_header = request.headers.get("Range")
    if range_header:
        m = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else min(start + 1024 * 1024, file_size - 1)
            end = min(end, file_size - 1)
            length = end - start + 1

            with open(file_path, "rb") as f:
                f.seek(start)
                data = f.read(length)

            rv = Response(data, 206, mimetype=mime_type)
            rv.headers.add("Content-Range", f"bytes {start}-{end}/{file_size}")
            rv.headers.add("Accept-Ranges", "bytes")
            rv.headers.add("Content-Length", str(length))
            return rv

    # 完整文件响应
    def generate():
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk

    rv = Response(generate(), 200, mimetype=mime_type)
    rv.headers.add("Accept-Ranges", "bytes")
    rv.headers.add("Content-Length", str(file_size))
    return rv


@app.route("/api/douyin/status", methods=["GET"])
def douyin_status():
    return jsonify({
        "authenticated": browser_publisher.is_authenticated(),
        "login_in_progress": _login_in_progress,
    })


@app.route("/api/douyin/login", methods=["POST"])
def douyin_login():
    global _login_in_progress, _login_result
    if _login_in_progress:
        return jsonify({"error": "登录正在进行中"}), 400

    _login_in_progress = True
    _login_result = None

    def do_login():
        global _login_in_progress, _login_result
        try:
            _login_result = browser_publisher.start_login()
            if _login_result:
                logger.log_auth("扫码登录", "成功")
            else:
                logger.log_auth("扫码登录", "失败", "超时或用户取消")
        except Exception as e:
            _login_result = False
            logger.log_auth("扫码登录", "失败", str(e))
        finally:
            _login_in_progress = False

    thread = threading.Thread(target=do_login, daemon=True)
    thread.start()

    logger.log_auth("扫码登录", "启动")
    return jsonify({"success": True, "message": "浏览器已打开，请扫码登录"})


@app.route("/api/douyin/login/status", methods=["GET"])
def douyin_login_status():
    return jsonify({
        "in_progress": _login_in_progress,
        "result": _login_result,
    })


@app.route("/api/publish", methods=["POST"])
def publish_video():
    data = request.json
    video_path = data.get("video_path", "").replace("\\", "/")
    title = data.get("title", "")
    description = data.get("description", "")
    is_manual = data.get("is_manual", True)

    if not video_path:
        return jsonify({"error": "未指定视频路径"}), 400

    video_name = Path(video_path).name

    # 定时发布去重检查（手动发布不受限制）
    if not is_manual and publish_tracker.was_scheduled(video_name):
        return jsonify({"error": "该视频已通过定时任务发布", "skipped": True}), 400

    if not browser_publisher.is_authenticated():
        logger.log_publish(title, "失败", "未授权")
        return jsonify({"error": "未授权，请先扫码登录抖音"}), 400

    result = browser_publisher.upload_video(video_path, title, description)

    if "error" in result:
        logger.log_publish(video_name, "失败", result["error"])
        return jsonify({"error": result["error"]}), 400

    publish_type = "manual" if is_manual else "scheduled"
    publish_tracker.record_publish(video_name, publish_type)
    logger.log_publish(video_name, "成功")
    return jsonify({"success": True, "result": result})


@app.route("/api/published", methods=["GET"])
def get_published():
    records = publish_tracker.get_all()
    return jsonify({"records": records})


@app.route("/api/published/clear", methods=["POST"])
def clear_published():
    publish_tracker.clear()
    logger.log_operation("清除发布记录")
    return jsonify({"success": True})


# ==================== 账号管理 API ====================

@app.route("/api/accounts", methods=["GET"])
def list_accounts():
    accounts = account_manager.list_accounts()
    return jsonify({
        "accounts": [asdict(a) for a in accounts],
        "active_account": account_manager._active_account_id,
    })


@app.route("/api/accounts/current", methods=["GET"])
def current_account():
    active = account_manager.get_active_account()
    if active:
        return jsonify(asdict(active))
    return jsonify({"account_id": None, "nickname": "默认账号", "is_active": False})


@app.route("/api/accounts/add", methods=["POST"])
def add_account():
    data = request.json or {}
    nickname = data.get("nickname", "")
    account = account_manager.add_account(nickname)
    logger.log_operation("添加账号", f"昵称: {account.nickname}")
    return jsonify({"success": True, "account": asdict(account)})


@app.route("/api/accounts/switch", methods=["POST"])
def switch_account():
    global browser_publisher
    data = request.json
    account_id = data.get("account_id")
    if not account_id:
        return jsonify({"error": "未指定账号ID"}), 400

    account = account_manager.switch_account(account_id)
    if not account:
        return jsonify({"error": "账号不存在"}), 404

    browser_publisher.close()
    browser_publisher = BrowserPublisher(cookie_dir=account.cookie_dir)

    logger.log_operation("切换账号", f"切换到: {account.nickname}")
    return jsonify({"success": True, "account": asdict(account)})


@app.route("/api/accounts/remove", methods=["POST"])
def remove_account():
    data = request.json
    account_id = data.get("account_id")
    if not account_id:
        return jsonify({"error": "未指定账号ID"}), 400

    if account_manager.remove_account(account_id):
        logger.log_operation("删除账号", f"ID: {account_id}")
        return jsonify({"success": True})
    return jsonify({"error": "账号不存在"}), 404


@app.route("/api/accounts/login", methods=["POST"])
def account_login():
    global _login_in_progress, _login_result, browser_publisher
    data = request.json or {}
    account_id = data.get("account_id")

    if _login_in_progress:
        return jsonify({"error": "登录正在进行中"}), 400

    if account_id:
        account = account_manager.switch_account(account_id)
        if not account:
            return jsonify({"error": "账号不存在"}), 404
        browser_publisher.close()
        browser_publisher = BrowserPublisher(cookie_dir=account.cookie_dir)

    _login_in_progress = True
    _login_result = None

    def do_login():
        global _login_in_progress, _login_result
        try:
            _login_result = browser_publisher.start_login()
            if _login_result:
                logger.log_auth("扫码登录", "成功")
            else:
                logger.log_auth("扫码登录", "失败", "超时或用户取消")
        except Exception as e:
            _login_result = False
            logger.log_auth("扫码登录", "失败", str(e))
        finally:
            _login_in_progress = False

    thread = threading.Thread(target=do_login, daemon=True)
    thread.start()

    logger.log_auth("扫码登录", "启动")
    return jsonify({"success": True, "message": "浏览器已打开，请扫码登录"})


@app.route("/api/accounts/create-and-login", methods=["POST"])
def create_and_login():
    """先扫码登录，成功后才创建账号"""
    global _create_login_in_progress, _create_login_result, _create_login_account
    global browser_publisher

    if _create_login_in_progress:
        return jsonify({"error": "登录正在进行中"}), 400

    if _login_in_progress:
        return jsonify({"error": "登录正在进行中"}), 400

    # 创建临时 cookie 目录
    temp_dir = account_manager.create_temp_cookie_dir()

    _create_login_in_progress = True
    _create_login_result = None
    _create_login_account = None

    def do_create_login():
        global _create_login_in_progress, _create_login_result, _create_login_account
        global browser_publisher
        try:
            # 用临时目录启动浏览器登录
            temp_publisher = BrowserPublisher(cookie_dir=temp_dir)
            success, username = temp_publisher.start_login_and_get_username()

            if not success:
                _create_login_result = "failed"
                account_manager.cleanup_temp_dir(temp_dir)
                logger.log_auth("添加账号", "失败", "登录超时或用户取消")
                return

            # 登录成功，确定用户名
            if not username:
                # Fallback：尝试从现有账号数量生成名称
                count = len(account_manager.list_accounts()) + 1
                username = f"抖音账号 {count}"
                logger.log_auth("添加账号", "成功", f"用户名抓取失败，使用默认名称: {username}")
            else:
                logger.log_auth("添加账号", "成功", f"用户名: {username}")

            # 升级临时目录为正式账号
            account = account_manager.promote_temp_to_account(temp_dir, username)
            if not account:
                _create_login_result = "failed"
                logger.log_auth("添加账号", "失败", "创建账号目录失败")
                return

            # 切换到新账号并刷新 browser_publisher
            browser_publisher.close()
            browser_publisher = BrowserPublisher(cookie_dir=account.cookie_dir)

            _create_login_account = asdict(account)
            _create_login_result = "success"

        except Exception as e:
            _create_login_result = "failed"
            account_manager.cleanup_temp_dir(temp_dir)
            logger.log_auth("添加账号", "失败", str(e))
        finally:
            _create_login_in_progress = False

    thread = threading.Thread(target=do_create_login, daemon=True)
    thread.start()

    logger.log_auth("添加账号", "启动")
    return jsonify({"success": True, "message": "浏览器已打开，请扫码登录"})


@app.route("/api/accounts/create-and-login/status", methods=["GET"])
def create_and_login_status():
    """查询创建并登录的状态"""
    return jsonify({
        "in_progress": _create_login_in_progress,
        "result": _create_login_result,
        "account": _create_login_account,
    })


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
            if publish_tracker.was_scheduled(video.filename):
                logger.log_scheduler("执行", f"跳过已发布视频: {video.filename}")
                return

            if browser_publisher.is_authenticated():
                logger.log_scheduler("执行", f"发布视频: {video.filename}")
                result = browser_publisher.upload_video(video.path.replace("\\", "/"), video.filename, "")
                if "error" in result:
                    logger.log_publish(video.filename, "失败", result["error"])
                else:
                    publish_tracker.record_publish(video.filename, "scheduled")
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
