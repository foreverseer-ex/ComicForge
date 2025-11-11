"""配置设置包。

包含应用的各项配置设置类。
"""
import json
import secrets
import string
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from .civitai_setting import CivitaiSettings
from .sd_forge_setting import SdForgeSettings
from .llm_setting import LlmSettings
from .draw_setting import DrawSettings
from .admin_setting import AdminSettings
from .ratelimit_setting import RateLimitSettings


def generate_strong_password(length: int = 32) -> str:
    """生成强密码。
    
    :param length: 密码长度，默认 32 位
    :return: 包含字母、数字、符号的随机密码
    """
    # 定义字符集：大小写字母、数字、符号
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # 确保密码包含至少一个大写字母、小写字母、数字和符号
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation),
    ]
    # 填充剩余长度
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    # 打乱顺序
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


class AppSettings(BaseModel):
    """应用全局配置类。
    
    包含所有子系统的配置。
    """
    civitai: CivitaiSettings = CivitaiSettings()
    sd_forge: SdForgeSettings = SdForgeSettings()
    llm: LlmSettings = LlmSettings()
    draw: DrawSettings = DrawSettings()
    admin: AdminSettings = AdminSettings()
    ratelimit: RateLimitSettings = RateLimitSettings()
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "AppSettings":
        """从配置文件加载配置。
        
        如果配置文件不存在，会创建默认配置并生成强密码。
        
        :param config_path: 配置文件路径，默认为项目根目录下的 config.json
        :return: AppSettings 实例
        """
        if config_path is None:
            # 默认使用项目根目录下的 config.json
            # 从 src/api/settings/__init__.py 向上查找项目根目录（包含 pyproject.toml 或 package.json）
            current = Path(__file__).parent.parent.parent  # src/
            # 继续向上查找，直到找到项目根目录
            while current.parent != current:
                if (current / "pyproject.toml").exists() or (current / "package.json").exists():
                    break
                current = current.parent
            project_root = current
            config_path = project_root / "config.json"
        
        if not config_path.exists():
            # 创建默认配置，生成强密码
            settings = cls()
            settings.admin.password = generate_strong_password(32)
            # 保存到文件
            settings.save(config_path, reason="初始化默认配置")
            return settings
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return cls(**data)
            
        except Exception as e:
            logger.exception(f"加载配置失败: {e}，使用默认配置")
            return cls()
    
    def save(self, config_path: Optional[Path] = None, reason: Optional[str] = None) -> bool:
        """将配置保存到文件。
        
        :param config_path: 配置文件路径，默认为项目根目录下的 config.json
        :param reason: 保存原因（用于日志记录）
        :return: 是否成功保存
        """
        if config_path is None:
            # 默认使用项目根目录下的 config.json
            # 从 src/api/settings/__init__.py 向上查找项目根目录（包含 pyproject.toml 或 package.json）
            current = Path(__file__).parent.parent.parent  # src/
            # 继续向上查找，直到找到项目根目录
            while current.parent != current:
                if (current / "pyproject.toml").exists() or (current / "package.json").exists():
                    break
                current = current.parent
            project_root = current
            config_path = project_root / "config.json"
        
        try:
            # 确保目录存在
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.exception(f"保存配置失败: {e}")
            return False


# 全局应用配置实例（使用模块级别的变量缓存，确保只加载一次）
_app_settings: Optional[AppSettings] = None

def get_app_settings() -> AppSettings:
    """获取应用配置实例（单例模式）。"""
    global _app_settings
    if _app_settings is None:
        _app_settings = AppSettings.load()
    return _app_settings

# 在模块级别直接调用，确保配置在导入时加载
app_settings = get_app_settings()


__all__ = [
    'app_settings',
    'AppSettings',
    'CivitaiSettings',
    'SdForgeSettings',
    'LlmSettings',
    'DrawSettings',
    'AdminSettings',
    'RateLimitSettings',
    'generate_strong_password',
]
