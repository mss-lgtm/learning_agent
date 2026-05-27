import tkinter as tk
from tkinter import messagebox
import sys
import os

from core.config import ConfigManager
from gui.main_window import MainWindow
from gui.tray_icon import TrayIcon
from utils.helpers import set_autostart, is_autostart_enabled


class TikTokPublisherApp:
    def __init__(self):
        self.config = ConfigManager()
        self.root: tk.Tk = None
        self.main_window: MainWindow = None
        self.tray_icon: TrayIcon = None

    def run(self):
        # 设置自启动
        if self.config.config.auto_start and not is_autostart_enabled():
            set_autostart(True)

        # 创建主窗口
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏窗口直到完全初始化

        # 创建主窗口
        self.main_window = MainWindow(self.root, self.config)

        # 创建系统托盘
        self.tray_icon = TrayIcon(
            on_show=self._show_window,
            on_exit=self._exit_app,
        )

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 显示窗口
        self.root.deiconify()

        # 启动托盘图标
        if self.config.config.minimize_to_tray:
            self.tray_icon.start()

        # 启动主循环
        self.root.mainloop()

    def _show_window(self):
        """从托盘显示窗口"""
        self.root.after(0, self._restore_window)

    def _restore_window(self):
        """恢复窗口显示"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _on_close(self):
        """窗口关闭事件"""
        if self.config.config.minimize_to_tray:
            self.root.withdraw()
            self.tray_icon.update_tooltip("抖音视频自动发布工具 - 运行中")
        else:
            self._exit_app()

    def _exit_app(self):
        """退出应用"""
        if self.main_window and self.main_window.scheduler:
            self.main_window.scheduler.stop()

        if self.tray_icon:
            self.tray_icon.stop()

        if self.root:
            self.root.destroy()

        sys.exit(0)


def main():
    app = TikTokPublisherApp()
    app.run()


if __name__ == "__main__":
    main()
