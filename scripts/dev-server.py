#!/usr/bin/env python3
"""
FastAPI 开发服务器启动脚本（优化重载速度）

只监听必要的目录，排除不需要的文件和目录，提高重载速度。
"""
import subprocess
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 只监听这些目录的变化
RELOAD_DIRS = [
    "src/api",
]

# 排除这些目录和文件（使用 glob 模式）
RELOAD_EXCLUDE = [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/.git/**",
    "**/node_modules/**",
    "**/storage/**",
    "**/tests/**",
    "**/desperate/**",  # 旧的 Flet 代码，不需要监听
    "**/resources/**",  # 资源文件，不需要监听
    "**/.venv/**",
    "**/venv/**",
    "**/env/**",
    "**/.env",
    "**/*.db",
    "**/*.db-journal",
]

# 构建 uvicorn 命令
cmd = [
    sys.executable, "-m", "uvicorn",
    "api.main:app",
    "--reload",
    "--host", "127.0.0.1",
    "--port", "7864",
    "--app-dir", str(PROJECT_ROOT / "src"),
]

# 添加重载目录
for reload_dir in RELOAD_DIRS:
    cmd.extend(["--reload-dir", str(PROJECT_ROOT / reload_dir)])

# 添加排除模式
for exclude_pattern in RELOAD_EXCLUDE:
    cmd.extend(["--reload-exclude", exclude_pattern])

# 运行命令
print("🚀 启动 FastAPI 开发服务器（优化重载）...")
print(f"📁 监听目录: {', '.join(RELOAD_DIRS)}")
print(f"🚫 排除模式: {len(RELOAD_EXCLUDE)} 个")
print()
subprocess.run(cmd, cwd=PROJECT_ROOT)

