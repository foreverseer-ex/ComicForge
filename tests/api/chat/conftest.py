"""
聊天测试的共享 fixtures。
"""
import sys
import os
from pathlib import Path

# 设置 UTF-8 编码
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加 src 目录到 Python 路径
# 从 conftest.py 的位置向上找到项目根目录
current_file = Path(__file__).resolve()
# conftest.py 在 tests/api/chat/conftest.py
# 向上: tests/api/chat/ -> tests/api/ -> tests/ -> ComicForge/
chat_test_dir = current_file.parent  # tests/api/chat/
api_test_dir = chat_test_dir.parent  # tests/api/
tests_dir = api_test_dir.parent  # tests/
project_root = tests_dir.parent  # ComicForge/
src_path = project_root / "src"

if not src_path.exists():
    raise ImportError(f"src 目录不存在: {src_path}")

# 移除可能冲突的路径
paths_to_remove = [str(tests_dir), str(api_test_dir), str(chat_test_dir)]
for p in paths_to_remove:
    if p in sys.path:
        sys.path.remove(p)

# 确保 src 在路径最前面
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 验证 api 模块可以导入
try:
    import api
    # 验证是从正确的路径导入的
    if hasattr(api, '__file__') and api.__file__:
        api_path = Path(api.__file__).parent
        if "src" not in str(api_path):
            raise ImportError(f"api 模块路径错误: {api_path}，应该从 src/api 导入")
except ImportError as e:
    raise ImportError(f"无法导入 api 模块: {e}，src_path={src_path}")

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.services.db.base import init_db
from api.services.db import ProjectService, HistoryService
from api.schemas.project import Project
from api.utils.path import project_home


@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture(scope="module")
def test_project():
    """创建测试项目"""
    project_id = "test-chat-api"
    
    # 清理旧数据
    existing_project = ProjectService.get(project_id)
    if existing_project:
        ProjectService.delete(project_id)
    
    # 初始化数据库
    init_db()
    
    # 创建新项目
    project_path = project_home / project_id
    project = Project(
        project_id=project_id,
        title="聊天API测试项目",
        author="测试作者",
        total_lines=1000,
        total_chapters=10,
        project_path=str(project_path)
    )
    created = ProjectService.create(project)
    
    yield created
    
    # 清理
    ProjectService.delete(project_id)
    HistoryService.clear(project_id)


@pytest.fixture(autouse=True)
def setup_database():
    """每个测试前初始化数据库"""
    init_db()
    yield
