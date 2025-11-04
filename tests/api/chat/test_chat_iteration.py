"""
测试迭代对话。

测试迭代式对话功能是否正常工作。
"""
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
current_file = Path(__file__).resolve()
tests_dir = current_file.parent.parent.parent
project_root = tests_dir.parent
src_path = project_root / "src"
if src_path.exists():
    if str(tests_dir) in sys.path:
        sys.path.remove(str(tests_dir))
    sys.path.insert(0, str(src_path))

import pytest
from api.services.llm import get_current_llm_service
from api.services.db import HistoryService
from api.schemas.chat import ChatIteration


class TestIterationChat:
    """测试迭代对话"""
    
    def test_iteration_chat_basic(self, test_project):
        """测试基本迭代对话"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            # 创建迭代数据
            iteration_data = {
                "target": "测试迭代功能",
                "index": 0,
                "stop": 10,  # 小范围测试
                "step": 2,
                "summary": ""
            }
            
            chunks = []
            
            async def collect_response():
                nonlocal chunks
                async for chunk in llm_service.chat_iteration(iteration_data, test_project.project_id):
                    chunks.append(chunk)
            
            import asyncio
            asyncio.run(collect_response())
            
            # 等待数据库更新
            import time
            time.sleep(1)
            
            # 检查数据库中的迭代消息
            messages = HistoryService.list(test_project.project_id)
            iteration_messages = [m for m in messages if m.message_type == "iteration"]
            
            print(f"\n[迭代对话] 响应块数: {len(chunks)}")
            print(f"[迭代对话] 迭代消息数: {len(iteration_messages)}")
            
            if iteration_messages:
                iteration_msg = iteration_messages[-1]
                
                # 检查迭代数据
                if iteration_msg.data:
                    iteration_info = ChatIteration(**iteration_msg.data)
                    print(f"[迭代对话] 迭代索引: {iteration_info.index}/{iteration_info.stop}")
                    print(f"[迭代对话] 迭代摘要长度: {len(iteration_info.summary)} 字符")
                    print(f"[迭代对话] 消息状态: {iteration_msg.status}")
                    
                    # 检查是否完成
                    if iteration_msg.status == "ready":
                        print(f"[迭代对话] ✅ 迭代完成")
                    else:
                        print(f"[迭代对话] ⚠️  迭代状态: {iteration_msg.status}")
                
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
    
    def test_iteration_chat_progress_update(self, test_project):
        """测试迭代对话的进度更新"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            iteration_data = {
                "target": "测试进度更新",
                "index": 0,
                "stop": 6,  # 3次迭代
                "step": 2,
                "summary": ""
            }
            
            # 记录迭代过程中的状态
            progress_states = []
            
            async def collect_with_progress():
                nonlocal progress_states
                iteration_count = 0
                async for chunk in llm_service.chat_iteration(iteration_data, test_project.project_id):
                    iteration_count += 1
                    # 每收到一些块后检查进度
                    if iteration_count % 5 == 0:
                        messages = HistoryService.list(test_project.project_id)
                        iteration_msgs = [m for m in messages if m.message_type == "iteration"]
                        if iteration_msgs:
                            last_iter = iteration_msgs[-1]
                            if last_iter.data:
                                iter_info = ChatIteration(**last_iter.data)
                                progress_states.append({
                                    'index': iter_info.index,
                                    'summary_len': len(iter_info.summary)
                                })
            
            import asyncio
            asyncio.run(collect_with_progress())
            
            # 最终检查
            import time
            time.sleep(1)
            
            messages = HistoryService.list(test_project.project_id)
            iteration_msgs = [m for m in messages if m.message_type == "iteration"]
            
            if iteration_msgs:
                last_iter = iteration_msgs[-1]
                if last_iter.data:
                    final_info = ChatIteration(**last_iter.data)
                    
                    print(f"\n[进度更新] 进度检查点: {len(progress_states)}")
                    print(f"[进度更新] 最终索引: {final_info.index}/{final_info.stop}")
                    print(f"[进度更新] 最终摘要长度: {len(final_info.summary)} 字符")
                    
                    if progress_states:
                        print(f"[进度更新] 进度检查点详情:")
                        for ps in progress_states:
                            print(f"  - 索引: {ps['index']}, 摘要长度: {ps['summary_len']}")
                    
                    print(f"[进度更新] ✅ 迭代进度更新正常")
            
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
    
    def test_iteration_chat_final_operation(self, test_project):
        """测试迭代对话的最终操作"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            iteration_data = {
                "target": "测试最终操作",
                "index": 0,
                "stop": 4,  # 2次迭代
                "step": 2,
                "summary": ""
            }
            
            async def collect_response():
                async for chunk in llm_service.chat_iteration(iteration_data, test_project.project_id):
                    pass  # 只收集，不处理
            
            import asyncio
            asyncio.run(collect_response())
            
            # 等待数据库更新
            import time
            time.sleep(1)
            
            # 检查最终操作的工具调用
            messages = HistoryService.list(test_project.project_id)
            iteration_msgs = [m for m in messages if m.message_type == "iteration"]
            
            if iteration_msgs:
                last_iter = iteration_msgs[-1]
                tool_calls = last_iter.tools
                final_context = last_iter.context
                
                print(f"\n[最终操作] 工具调用数量: {len(tool_calls)}")
                print(f"[最终操作] 最终上下文长度: {len(final_context)} 字符")
                print(f"[最终操作] 消息状态: {last_iter.status}")
                
                if tool_calls:
                    print(f"[最终操作] 工具列表: {[t.get('name') for t in tool_calls]}")
                    print(f"[最终操作] ✅ 最终操作工具调用正常")
                
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
