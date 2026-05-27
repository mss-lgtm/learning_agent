import pystray
from PIL import Image, ImageDraw
import threading
from typing import Callable, Optional


class TrayIcon:
    def __init__(self, on_show: Callable, on_exit: Callable):
        self.on_show = on_show
        self.on_exit = on_exit
        self.icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def _create_image(self) -> Image.Image:
        # 创建一个简单的图标
        width = 64
        height = 64
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 绘制一个简单的抖音风格图标
        draw.rounded_rectangle([8, 8, 56, 56], radius=10, fill="#FE2C55")
        draw.text((20, 20), "抖", fill="white")

        return image

    def _create_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("显示主窗口", self._show_window),
            pystray.MenuItem("退出", self._exit_app),
        )

    def _show_window(self, icon=None, item=None):
        self.on_show()

    def _exit_app(self, icon=None, item=None):
        if self.icon:
            self.icon.stop()
        self.on_exit()

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self.icon = pystray.Icon(
            name="抖音发布工具",
            icon=self._create_image(),
            title="抖音视频自动发布工具",
            menu=self._create_menu(),
        )
        self.icon.run()

    def stop(self):
        if self.icon:
            self.icon.stop()

    def update_tooltip(self, text: str):
        if self.icon:
            self.icon.title = text
