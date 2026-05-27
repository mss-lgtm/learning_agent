import base64
import hashlib
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptoManager:
    """加密管理器 - 用于敏感信息的加密存储"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 密钥文件位置
        self.key_dir = Path(os.environ.get("APPDATA", "")) / "TikTokPublisher"
        self.key_file = self.key_dir / ".secret_key"
        self.salt_file = self.key_dir / ".salt"

        # 初始化加密器
        self._fernet = None
        self._init_encryption()

    def _init_encryption(self):
        """初始化加密系统"""
        self.key_dir.mkdir(parents=True, exist_ok=True)

        # 获取或生成盐值
        salt = self._get_or_create_salt()

        # 获取或生成密钥
        key = self._get_or_create_key(salt)

        # 创建Fernet加密器
        self._fernet = Fernet(key)

    def _get_or_create_salt(self) -> bytes:
        """获取或创建盐值"""
        if self.salt_file.exists():
            return self.salt_file.read_bytes()
        else:
            salt = os.urandom(16)
            self.salt_file.write_bytes(salt)
            # 设置为隐藏文件
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(self.salt_file), 2)
            except:
                pass
            return salt

    def _get_or_create_key(self, salt: bytes) -> bytes:
        """获取或创建加密密钥"""
        if self.key_file.exists():
            return self.key_file.read_bytes()
        else:
            # 使用机器特定信息生成密钥
            password = self._get_machine_id()

            # 使用PBKDF2派生密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

            # 保存密钥
            self.key_file.write_bytes(key)
            # 设置为隐藏文件
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(self.key_file), 2)
            except:
                pass
            return key

    def _get_machine_id(self) -> str:
        """获取机器唯一标识"""
        import platform

        # 组合多个机器特征
        parts = [
            platform.node(),  # 计算机名
            platform.machine(),  # 机器架构
            str(os.getuid()) if hasattr(os, 'getuid') else '',  # 用户ID
        ]

        # 如果在Windows上，添加更多标识
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            parts.append(machine_guid)
            winreg.CloseKey(key)
        except:
            pass

        # 生成哈希
        raw_id = "-".join(filter(None, parts))
        return hashlib.sha256(raw_id.encode()).hexdigest()

    def encrypt(self, plaintext: str) -> str:
        """加密字符串"""
        if not plaintext:
            return ""
        encrypted = self._fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """解密字符串"""
        if not ciphertext:
            return ""
        try:
            encrypted = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = self._fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception:
            # 如果解密失败，可能是旧的明文数据，直接返回
            return ciphertext

    def is_encrypted(self, text: str) -> bool:
        """检查文本是否已加密"""
        if not text:
            return False
        try:
            # 尝试解密
            encrypted = base64.urlsafe_b64decode(text.encode())
            self._fernet.decrypt(encrypted)
            return True
        except:
            return False


# 全局实例
crypto = CryptoManager()
