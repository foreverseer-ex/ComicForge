#!/bin/bash
# FastAPI 开发服务器启动脚本（Linux/Mac，优化重载速度）

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 只监听 src/api 目录，排除不需要的文件
echo "🚀 启动 FastAPI 开发服务器（优化重载）..."
echo "📁 监听目录: src/api"
echo "🚫 排除: __pycache__, storage, tests, desperate, resources 等"
echo ""

uv run uvicorn api.main:app \
    --reload \
    --host 127.0.0.1 \
    --port 7864 \
    --app-dir src \
    --reload-dir src/api \
    --reload-exclude "**/__pycache__/**" \
    --reload-exclude "**/*.pyc" \
    --reload-exclude "**/.git/**" \
    --reload-exclude "**/node_modules/**" \
    --reload-exclude "**/storage/**" \
    --reload-exclude "**/tests/**" \
    --reload-exclude "**/desperate/**" \
    --reload-exclude "**/resources/**" \
    --reload-exclude "**/.venv/**" \
    --reload-exclude "**/venv/**" \
    --reload-exclude "**/env/**" \
    --reload-exclude "**/*.db" \
    --reload-exclude "**/*.db-journal"

