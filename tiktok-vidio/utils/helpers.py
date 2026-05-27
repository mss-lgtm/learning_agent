import sys
import ctypes
import winreg
from pathlib import Path


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()


def set_autostart(enable: bool, app_name: str = "TikTokPublisher"):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)

        if enable:
            exe_path = Path(sys.executable).parent / "TikTokPublisher.exe"
            if exe_path.exists():
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, str(exe_path))
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass

        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"设置自启动失败: {e}")
        return False


def is_autostart_enabled(app_name: str = "TikTokPublisher") -> bool:
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def get_app_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def format_file_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
