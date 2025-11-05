"""配置设置包。

包含应用的各项配置设置类。
"""
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from .civitai_setting import CivitaiSettings
from .sd_forge_setting import SdForgeSettings
from .llm_setting import LlmSettings
from .draw_setting import DrawSettings
from .frontend_setting import FrontendSettings


class AppSettings(BaseModel):
    """应用全局配置类。
    
    包含所有子系统的配置。
    """
    civitai: CivitaiSettings = CivitaiSettings()
    sd_forge: SdForgeSettings = SdForgeSettings()
    llm: LlmSettings = LlmSettings()
    draw: DrawSettings = DrawSettings()
    frontend: FrontendSettings = FrontendSettings()
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "AppSettings":
        """从配置文件加载配置。
        
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
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return cls()
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            logger.success(f"配置加载成功: {config_path}")
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
            
            if reason:
                logger.debug(f"配置已保存: {reason}")
            else:
                logger.debug(f"配置已保存: {config_path}")
            return True
            
        except Exception as e:
            logger.exception(f"保存配置失败: {e}")
            return False


# 全局应用配置实例
app_settings = AppSettings.load()


__all__ = [
    'app_settings',
    'AppSettings',
    'CivitaiSettings',
    'SdForgeSettings',
    'LlmSettings',
    'DrawSettings',
    'FrontendSettings',
]
