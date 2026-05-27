import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Optional
from datetime import datetime
import threading

from core.config import ConfigManager
from core.video_scanner import VideoScanner, VideoFile
from core.browser_publisher import BrowserPublisher
from core.scheduler import TaskScheduler


class MainWindow:
    def __init__(self, root: tk.Tk, config_manager: ConfigManager):
        self.root = root
        self.config = config_manager
        self.scanner: Optional[VideoScanner] = None
        self.publisher = BrowserPublisher(cookie_dir=self.config.config.douyin.cookie_dir)
        self.scheduler = TaskScheduler()

        self._setup_window()
        self._create_widgets()
        self._load_config()
        self._start_scheduler()

    def _setup_window(self):
        self.root.title("抖音视频自动发布工具")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)

        # 设置图标（如果存在）
        try:
            self.root.iconbitmap("assets/icon.ico")
        except:
            pass

    def _create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部配置区域
        self._create_config_section(main_frame)

        # 中间视频列表区域
        self._create_video_section(main_frame)

        # 底部状态栏
        self._create_status_bar()

    def _create_config_section(self, parent):
        # 配置区域框架
        config_frame = ttk.LabelFrame(parent, text="配置", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # 第一行：视频目录
        dir_frame = ttk.Frame(config_frame)
        dir_frame.pack(fill=tk.X, pady=5)

        ttk.Label(dir_frame, text="视频目录:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=50)
        self.dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(dir_frame, text="浏览", command=self._browse_directory).pack(side=tk.LEFT)

        # 第二行：定时配置
        schedule_frame = ttk.Frame(config_frame)
        schedule_frame.pack(fill=tk.X, pady=5)

        ttk.Label(schedule_frame, text="定时发布:").pack(side=tk.LEFT)

        self.schedule_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(schedule_frame, text="启用", variable=self.schedule_enabled_var).pack(side=tk.LEFT, padx=5)

        ttk.Label(schedule_frame, text="每").pack(side=tk.LEFT)
        self.days_var = tk.StringVar(value="周二,周四")
        days_combo = ttk.Combobox(schedule_frame, textvariable=self.days_var, width=10,
                                  values=["周一,周三,周五", "周二,周四", "每天", "工作日"])
        days_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(schedule_frame, text="的").pack(side=tk.LEFT)
        self.time_var = tk.StringVar(value="17:00")
        time_entry = ttk.Entry(schedule_frame, textvariable=self.time_var, width=8)
        time_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(schedule_frame, text="发布").pack(side=tk.LEFT)

        # 第三行：抖音配置
        douyin_frame = ttk.Frame(config_frame)
        douyin_frame.pack(fill=tk.X, pady=5)

        ttk.Label(douyin_frame, text="抖音配置:").pack(side=tk.LEFT)
        self.auth_status_var = tk.StringVar(value="未授权")
        ttk.Label(douyin_frame, textvariable=self.auth_status_var).pack(side=tk.LEFT, padx=5)

        ttk.Button(douyin_frame, text="扫码登录", command=self._authorize_douyin).pack(side=tk.LEFT, padx=5)

        # 保存按钮
        btn_frame = ttk.Frame(config_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="保存配置", command=self._save_config).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="立即发布", command=self._publish_now).pack(side=tk.LEFT, padx=10)

    def _create_video_section(self, parent):
        # 视频列表框架
        video_frame = ttk.LabelFrame(parent, text="视频列表", padding="10")
        video_frame.pack(fill=tk.BOTH, expand=True)

        # 工具栏
        toolbar = ttk.Frame(video_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar, text="刷新", command=self._refresh_videos).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="打开目录", command=self._open_directory).pack(side=tk.LEFT, padx=5)

        # 视频列表Treeview
        columns = ("filename", "size", "modified", "status")
        self.video_tree = ttk.Treeview(video_frame, columns=columns, show="headings", height=15)

        self.video_tree.heading("filename", text="文件名")
        self.video_tree.heading("size", text="大小")
        self.video_tree.heading("modified", text="修改时间")
        self.video_tree.heading("status", text="状态")

        self.video_tree.column("filename", width=300)
        self.video_tree.column("size", width=100)
        self.video_tree.column("modified", width=150)
        self.video_tree.column("status", width=100)

        scrollbar = ttk.Scrollbar(video_frame, orient=tk.VERTICAL, command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=scrollbar.set)

        self.video_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定双击事件
        self.video_tree.bind("<Double-1>", self._on_video_double_click)

    def _create_status_bar(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)

        self.scheduler_status_var = tk.StringVar(value="调度器: 未运行")
        ttk.Label(status_frame, textvariable=self.scheduler_status_var).pack(side=tk.RIGHT, padx=5)

    def _load_config(self):
        self.dir_var.set(self.config.config.video_directory)
        self.schedule_enabled_var.set(self.config.config.schedule.enabled)
        self.time_var.set(self.config.config.schedule.time)

        if self.config.config.video_directory:
            self._refresh_videos()

        if self.publisher.is_authenticated():
            self.auth_status_var.set("已登录")
        else:
            self.auth_status_var.set("未登录")

    def _browse_directory(self):
        directory = filedialog.askdirectory(title="选择视频目录")
        if directory:
            self.dir_var.set(directory)
            self.config.update_video_directory(directory)
            self._refresh_videos()

    def _refresh_videos(self):
        directory = self.dir_var.get()
        if not directory:
            messagebox.showwarning("警告", "请先选择视频目录")
            return

        self.scanner = VideoScanner(directory)
        videos = self.scanner.scan()

        # 清空列表
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)

        # 填充列表
        for video in videos:
            self.video_tree.insert("", tk.END, values=(
                video.filename,
                video.size_str,
                video.modified_str,
                "待发布"
            ))

        self.status_var.set(f"找到 {len(videos)} 个视频文件")

    def _open_directory(self):
        directory = self.dir_var.get()
        if directory:
            import os
            os.startfile(directory)

    def _on_video_double_click(self, event):
        selection = self.video_tree.selection()
        if selection:
            item = self.video_tree.item(selection[0])
            filename = item["values"][0]
            messagebox.showinfo("视频信息", f"文件: {filename}")

    def _authorize_douyin(self):
        self.auth_status_var.set("正在打开浏览器，请扫码登录...")
        self.root.update()

        def do_login():
            success = self.publisher.start_login()
            self.root.after(0, lambda: self._on_login_result(success))

        threading.Thread(target=do_login, daemon=True).start()

    def _on_login_result(self, success):
        if success:
            self.auth_status_var.set("已登录")
            messagebox.showinfo("成功", "登录成功！")
        else:
            self.auth_status_var.set("登录失败")
            messagebox.showerror("失败", "登录失败或超时，请重试")
        self.status_var.set("就绪")

    def _convert_days(self, days_str: str) -> list:
        """将中文天数转换为英文"""
        day_map = {
            "周一": "monday", "周二": "tuesday", "周三": "wednesday",
            "周四": "thursday", "周五": "friday", "周六": "saturday", "周日": "sunday"
        }
        if days_str == "每天":
            return list(day_map.values())
        if days_str == "工作日":
            return ["monday", "tuesday", "wednesday", "thursday", "friday"]

        days = []
        for day in days_str.split(","):
            day = day.strip()
            if day in day_map:
                days.append(day_map[day])
        return days

    def _save_config(self):
        # 保存所有配置
        self.config.update_video_directory(self.dir_var.get())

        # 转换天数
        days = self._convert_days(self.days_var.get())

        self.config.update_schedule(
            enabled=self.schedule_enabled_var.get(),
            days=days,
            time=self.time_var.get(),
        )
        self._update_scheduler()
        messagebox.showinfo("成功", "配置已保存")

    def _start_scheduler(self):
        self.scheduler.set_callback(self._scheduled_publish)
        self._update_scheduler()
        self.scheduler.start()
        self._update_scheduler_status()

    def _update_scheduler(self):
        self.scheduler.update_schedule(self.config.config.schedule)

    def _update_scheduler_status(self):
        status = self.scheduler.get_status()
        self.scheduler_status_var.set(
            f"调度器: {'运行中' if status['running'] else '已停止'} | "
            f"下次执行: {status['next_run']}"
        )
        self.root.after(60000, self._update_scheduler_status)

    def _scheduled_publish(self):
        """定时任务回调"""
        if not self.scanner:
            return

        video = self.scanner.get_latest_video()
        if video:
            self._publish_video(video)

    def _publish_now(self):
        """立即发布最新视频"""
        if not self.scanner:
            messagebox.showwarning("警告", "请先选择视频目录")
            return

        video = self.scanner.get_latest_video()
        if video:
            self._publish_video(video)
        else:
            messagebox.showinfo("提示", "没有找到视频文件")

    def _publish_video(self, video: VideoFile):
        """发布单个视频"""
        if not self.publisher.is_authenticated():
            messagebox.showwarning("警告", "请先扫码登录抖音")
            return

        self.status_var.set(f"正在发布: {video.filename}")

        # 弹出标题输入对话框
        title = simpledialog.askstring("视频标题", "请输入视频标题:", initialvalue=video.filename)
        if not title:
            return

        result = self.publisher.upload_video(
            video_path=video.path,
            title=title,
            description="",
        )

        if "error" in result:
            messagebox.showerror("发布失败", result["error"])
            self.status_var.set("发布失败")
        else:
            messagebox.showinfo("成功", f"视频 {video.filename} 已提交发布")
            self.status_var.set("发布成功")
            self._refresh_videos()
