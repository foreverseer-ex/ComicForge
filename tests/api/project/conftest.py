"""
项目管理测试的共享 fixtures。
"""
import sys
import os
from pathlib import Path

# 设置 UTF-8 编码
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加 src 目录到 Python 路径
current_file = Path(__file__).resolve()
project_test_dir = current_file.parent  # tests/api/project/
api_test_dir = project_test_dir.parent  # tests/api/
tests_dir = api_test_dir.parent  # tests/
project_root = tests_dir.parent  # ComicForge/
src_path = project_root / "src"

if not src_path.exists():
    raise ImportError(f"src 目录不存在: {src_path}")

# 移除可能冲突的路径
paths_to_remove = [str(tests_dir), str(api_test_dir), str(project_test_dir)]
for p in paths_to_remove:
    if p in sys.path:
        sys.path.remove(p)

# 确保 src 在路径最前面
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 验证 api 模块可以导入
try:
    import api
except ImportError as e:
    raise ImportError(f"无法导入 api 模块: {e}，src_path={src_path}")

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.services.db.base import init_db
from api.services.db import ProjectService


@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """每个测试前初始化数据库"""
    init_db()
    yield
