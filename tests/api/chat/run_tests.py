"""
运行聊天功能测试的脚本。

用于直接运行测试，避免 pytest 路径问题。
"""
import sys
import os
from pathlib import Path

# 设置 UTF-8 编码
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加 src 目录到 Python 路径
current_file = Path(__file__).resolve()
chat_test_dir = current_file.parent  # tests/api/chat/
api_test_dir = chat_test_dir.parent  # tests/api/
tests_dir = api_test_dir.parent  # tests/
project_root = tests_dir.parent  # ComicForge/
src_path = project_root / "src"

if not src_path.exists():
    print(f"错误: src 目录不存在: {src_path}")
    sys.exit(1)

# 移除可能冲突的路径
paths_to_remove = [str(tests_dir), str(api_test_dir), str(chat_test_dir)]
for p in paths_to_remove:
    if p in sys.path:
        sys.path.remove(p)

# 确保 src 在路径最前面
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 现在可以导入测试模块
if __name__ == "__main__":
    import subprocess
    
    # 使用 pytest 运行测试
    cmd = [
        sys.executable, "-m", "pytest",
        str(chat_test_dir),
        "-v",
        "-s"
    ]
    
    print(f"运行测试命令: {' '.join(cmd)}")
    print(f"工作目录: {project_root}")
    print(f"Python 路径: {sys.path[:3]}")
    print("\n" + "="*60)
    
    result = subprocess.run(cmd, cwd=str(project_root))
    sys.exit(result.returncode)
