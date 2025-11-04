"""
URL 和文件打开工具函数。
"""
import os
import platform
import subprocess
import webbrowser
from pathlib import Path

from loguru import logger


def launch_url_or_file(url: str, project_root: Path | None = None) -> None:
    """
    打开 URL 或本地文件。
    
    智能判断链接类型：
    - http/https → 使用默认浏览器打开网页
    - 本地文件路径 → 使用系统默认程序打开文件
    - 相对路径 → 基于 project_root 解析后打开
    
    Args:
        url: 要打开的 URL 或文件路径
        project_root: 项目根目录（用于解析相对路径），如果不提供则使用当前工作目录
    """
    if not url:
        return
    
    url = url.strip()
    
    # 1. 检查是否是网页链接
    if url.startswith(("http://", "https://")):
        webbrowser.open(url)
        return
    
    # 2. 本地文件或相对路径
    try:
        # 如果没有提供 project_root，尝试从当前工作目录推断
        if project_root is None:
            # 通常项目根目录包含 README.md 或 pyproject.toml
            cwd = Path.cwd()
            if (cwd / "README.md").exists() or (cwd / "pyproject.toml").exists():
                project_root = cwd
            else:
                # 默认使用当前工作目录
                project_root = cwd
        
        # 处理相对路径
        if not Path(url).is_absolute():
            file_path = project_root / url
        else:
            file_path = Path(url)
        
        # 检查文件是否存在
        if file_path.exists():
            # 使用系统默认程序打开
            if os.name == 'nt':  # Windows
                os.startfile(str(file_path))
            elif os.name == 'posix':  # Linux/macOS
                if platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', str(file_path)], check=False)
                else:  # Linux
                    subprocess.run(['xdg-open', str(file_path)], check=False)
        else:
            # 文件不存在，尝试作为网页打开
            webbrowser.open(url)
    except Exception:
        logger.exception(f"打开链接或文件失败: {url}")
        # 出错时尝试作为网页打开
        try:
            webbrowser.open(url)
        except Exception:
            logger.exception(f"尝试作为网页打开也失败: {url}")
