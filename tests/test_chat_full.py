"""
完整的聊天功能测试。

直接运行所有聊天功能测试，不依赖 pytest。
"""
import sys
import os
from pathlib import Path

# 设置 UTF-8 编码
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加 src 目录到 Python 路径
current_file = Path(__file__).resolve()
tests_dir = current_file.parent
project_root = tests_dir.parent
src_path = project_root / "src"

if not src_path.exists():
    print(f"错误: src 目录不存在: {src_path}")
    sys.exit(1)

# 移除可能冲突的路径
if str(tests_dir) in sys.path:
    sys.path.remove(str(tests_dir))
sys.path.insert(0, str(src_path))

from api.services.llm import get_current_llm_service
from api.services.db.base import init_db
from api.services.db import ProjectService, HistoryService, MemoryService
from api.schemas.project import Project
from api.schemas.chat import ChatMessage, ChatIteration
from api.utils.path import project_home
import uuid
import time

# 初始化数据库
init_db()

# 创建测试项目
project_id = "test-chat-full"
existing = ProjectService.get(project_id)
if existing:
    ProjectService.delete(project_id)

project_path = project_home / project_id
project = Project(
    project_id=project_id,
    title="完整聊天测试项目",
    author="测试作者",
    total_lines=1000,
    total_chapters=10,
    project_path=str(project_path)
)
test_project = ProjectService.create(project)

print("=" * 80)
print("开始完整聊天功能测试")
print("=" * 80)

llm_service = get_current_llm_service()
is_ready = llm_service.is_ready()

# ==================== 1. 测试直接聊天（invoke模式） ====================
print("\n[1] 测试直接聊天（invoke模式）...")
if is_ready:
    try:
        response = llm_service.simple_chat("你好，请简单介绍一下自己")
        print(f"  [OK] 响应长度: {len(response)} 字符")
        print(f"  [OK] 响应预览: {response[:100]}...")
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "timeout" in error_str:
            print(f"  [SKIP] 网络连接失败（这是正常的）: {type(e).__name__}")
        else:
            print(f"  [ERROR] 错误: {e}")
else:
    print(f"  [SKIP] LLM 服务未就绪")

# ==================== 2. 测试直接聊天+工具调用 ====================
print("\n[2] 测试直接聊天+工具调用...")
if is_ready:
    try:
        message = f"请获取项目 {project_id} 的标题"
        full_response = ""
        
        async def collect():
            nonlocal full_response
            async for chunk in llm_service.chat(message, project_id):
                full_response += chunk
        
        import asyncio
        asyncio.run(collect())
        
        time.sleep(0.5)  # 等待数据库更新
        
        messages = HistoryService.list(project_id)
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        if assistant_messages:
            last_msg = assistant_messages[-1]
            tool_calls = last_msg.tools
            
            print(f"  [OK] 响应长度: {len(full_response)} 字符")
            print(f"  [OK] 工具调用数量: {len(tool_calls)}")
            
            if tool_calls:
                print(f"  [OK] 工具列表: {[t.get('name') for t in tool_calls]}")
                print(f"  [OK] ✅ 检测到工具调用")
            else:
                print(f"  [WARN] 未检测到工具调用（可能LLM未调用工具）")
                
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "timeout" in error_str:
            print(f"  [SKIP] 网络连接失败: {type(e).__name__}")
        else:
            print(f"  [ERROR] 错误: {e}")
else:
    print(f"  [SKIP] LLM 服务未就绪")

# ==================== 3. 测试流式传输 ====================
print("\n[3] 测试流式传输（stream模式）...")
if is_ready:
    try:
        message = "请用一句话介绍自己"
        chunks = []
        
        async def collect_chunks():
            nonlocal chunks
            async for chunk in llm_service.chat(message, project_id):
                chunks.append(chunk)
        
        import asyncio
        asyncio.run(collect_chunks())
        
        print(f"  [OK] 收到 {len(chunks)} 个响应块")
        print(f"  [OK] 总长度: {sum(len(c) for c in chunks)} 字符")
        
        if chunks:
            print(f"  [OK] ✅ 流式传输正常")
            print(f"  [OK] 第一个块预览: {chunks[0][:50]}...")
            
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "timeout" in error_str:
            print(f"  [SKIP] 网络连接失败: {type(e).__name__}")
        else:
            print(f"  [ERROR] 错误: {e}")
else:
    print(f"  [SKIP] LLM 服务未就绪")

# ==================== 4. 测试流式传输+工具调用 ====================
print("\n[4] 测试流式传输+工具调用...")
if is_ready:
    try:
        message = f"请告诉我项目 {project_id} 有多少行和多少章节"
        chunks = []
        
        async def collect_with_tools():
            nonlocal chunks
            async for chunk in llm_service.chat(message, project_id):
                chunks.append(chunk)
        
        import asyncio
        asyncio.run(collect_with_tools())
        
        time.sleep(0.5)
        
        messages = HistoryService.list(project_id)
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        if assistant_messages:
            last_msg = assistant_messages[-1]
            tool_calls = last_msg.tools
            
            print(f"  [OK] 响应块数: {len(chunks)}")
            print(f"  [OK] 工具调用数量: {len(tool_calls)}")
            
            if tool_calls:
                for i, tool in enumerate(tool_calls):
                    print(f"  [OK] 工具 {i+1}: {tool.get('name')}")
                print(f"  [OK] ✅ 流式传输+工具调用正常")
            else:
                print(f"  [WARN] 未检测到工具调用")
                
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "timeout" in error_str:
            print(f"  [SKIP] 网络连接失败: {type(e).__name__}")
        else:
            print(f"  [ERROR] 错误: {e}")
else:
    print(f"  [SKIP] LLM 服务未就绪")

# ==================== 5. 测试迭代对话 ====================
print("\n[5] 测试迭代对话...")
if is_ready:
    try:
        iteration_data = {
            "target": "测试迭代功能",
            "index": 0,
            "stop": 6,  # 3次迭代
            "step": 2,
            "summary": ""
        }
        
        chunks = []
        
        async def collect_iteration():
            nonlocal chunks
            async for chunk in llm_service.chat_iteration(iteration_data, project_id):
                chunks.append(chunk)
        
        import asyncio
        asyncio.run(collect_iteration())
        
        time.sleep(0.5)
        
        messages = HistoryService.list(project_id)
        iteration_msgs = [m for m in messages if m.message_type == "iteration"]
        
        print(f"  [OK] 响应块数: {len(chunks)}")
        print(f"  [OK] 迭代消息数: {len(iteration_msgs)}")
        
        if iteration_msgs:
            last_iter = iteration_msgs[-1]
            if last_iter.data:
                iter_info = ChatIteration(**last_iter.data)
                print(f"  [OK] 迭代索引: {iter_info.index}/{iter_info.stop}")
                print(f"  [OK] 迭代摘要长度: {len(iter_info.summary)} 字符")
                print(f"  [OK] 消息状态: {last_iter.status}")
                print(f"  [OK] ✅ 迭代对话正常")
                
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "timeout" in error_str:
            print(f"  [SKIP] 网络连接失败: {type(e).__name__}")
        else:
            print(f"  [ERROR] 错误: {e}")
else:
    print(f"  [SKIP] LLM 服务未就绪")

# ==================== 6. 测试聊天总结 ====================
print("\n[6] 测试聊天总结...")
try:
    # 清空现有消息
    HistoryService.clear(project_id)
    
    # 创建足够多的消息来触发总结
    summary_epoch = 5  # 假设配置为5
    
    print(f"  [INFO] 创建 {summary_epoch * 2} 条消息来触发总结...")
    
    for i in range(summary_epoch * 2):
        user_msg = ChatMessage(
            message_id=str(uuid.uuid4()),
            project_id=project_id,
            role="user",
            context=f"用户消息 {i+1}",
            status="ready",
            message_type="normal"
        )
        HistoryService.create(user_msg)
        
        assistant_msg = ChatMessage(
            message_id=str(uuid.uuid4()),
            project_id=project_id,
            role="assistant",
            context=f"助手回复 {i+1}",
            status="ready",
            message_type="normal"
        )
        HistoryService.create(assistant_msg)
        
        # 在达到 epoch 倍数时触发总结
        current_count = HistoryService.count(project_id)
        if current_count % summary_epoch == 0 and is_ready:
            llm_service.summary_history(project_id)
            
            summary = MemoryService.get_summary(project_id)
            if summary and summary.data:
                print(f"  [OK] 消息数 {current_count} 时，总结已生成")
                print(f"  [OK] 总结长度: {len(summary.data)} 字符")
                print(f"  [OK] ✅ 聊天总结正常")
                break
    
    # 测试总结存储和检索
    test_summary = "测试总结内容"
    MemoryService.update_summary(project_id, test_summary)
    retrieved = MemoryService.get_summary(project_id)
    
    if retrieved and retrieved.data == test_summary:
        print(f"  [OK] ✅ 总结存储和检索正常")
    
except Exception as e:
    print(f"  [ERROR] 错误: {e}")

# ==================== 清理 ====================
print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

# 清理测试项目
ProjectService.delete(project_id)
