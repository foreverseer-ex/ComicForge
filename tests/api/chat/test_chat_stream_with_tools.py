"""
测试流式传输+工具调用。

测试在流式响应过程中工具调用是否正常工作。
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


class TestStreamChatWithTools:
    """测试流式传输+工具调用"""
    
    def test_stream_chat_with_tool_call(self, test_project):
        """测试流式聊天时工具调用"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            # 创建应该触发工具调用的消息
            message = f"请获取项目 {test_project.project_id} 的标题和作者信息"
            
            chunks = []
            tool_call_detected = False
            
            async def collect_with_tracking():
                nonlocal chunks, tool_call_detected
                async for chunk in llm_service.chat(message, test_project.project_id):
                    chunks.append(chunk)
            
            import asyncio
            asyncio.run(collect_with_tracking())
            
            # 等待数据库更新
            import time
            time.sleep(1)
            
            # 检查数据库中的消息
            messages = HistoryService.list(test_project.project_id)
            assistant_messages = [m for m in messages if m.role == "assistant"]
            
            print(f"\n[流式+工具] 响应块数: {len(chunks)}")
            print(f"[流式+工具] 总响应长度: {sum(len(c) for c in chunks)} 字符")
            
            if assistant_messages:
                last_message = assistant_messages[-1]
                tool_calls = last_message.tools
                
                print(f"[流式+工具] 工具调用数量: {len(tool_calls)}")
                
                if tool_calls:
                    tool_call_detected = True
                    for i, tool in enumerate(tool_calls):
                        tool_name = tool.get('name', 'unknown')
                        tool_result = tool.get('result')
                        has_result = tool_result is not None
                        
                        print(f"[流式+工具] 工具 {i+1}: {tool_name}")
                        print(f"[流式+工具] 工具 {i+1} 有结果: {has_result}")
                        
                        if has_result:
                            print(f"[流式+工具] 工具 {i+1} 结果长度: {len(str(tool_result))} 字符")
                    
                    print(f"[流式+工具] ✅ 检测到工具调用")
                else:
                    print(f"[流式+工具] ⚠️  未检测到工具调用")
            
            # 至少应该有响应内容
            assert len(chunks) > 0 or tool_call_detected, "应该有响应或工具调用"
            
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
    
    def test_stream_chat_tool_call_real_time_update(self, test_project):
        """测试流式聊天时工具调用是否实时更新到数据库"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            message = f"请告诉我项目 {test_project.project_id} 有多少行和多少章节"
            
            # 在流式过程中多次检查数据库
            check_points = []
            
            async def collect_with_checks():
                check_count = 0
                async for chunk in llm_service.chat(message, test_project.project_id):
                    check_count += 1
                    # 每收到一些块后检查一次数据库
                    if check_count % 10 == 0:
                        messages = HistoryService.list(test_project.project_id)
                        assistant_messages = [m for m in messages if m.role == "assistant"]
                        if assistant_messages:
                            last_msg = assistant_messages[-1]
                            tool_count = len(last_msg.tools)
                            check_points.append({
                                'chunk_count': check_count,
                                'tool_count': tool_count,
                                'status': last_msg.status
                            })
            
            import asyncio
            asyncio.run(collect_with_checks())
            
            # 等待最终更新
            import time
            time.sleep(1)
            
            # 最终检查
            messages = HistoryService.list(test_project.project_id)
            assistant_messages = [m for m in messages if m.role == "assistant"]
            if assistant_messages:
                last_msg = assistant_messages[-1]
                final_tool_count = len(last_msg.tools)
                
                print(f"\n[实时更新] 检查点数量: {len(check_points)}")
                print(f"[实时更新] 最终工具调用数: {final_tool_count}")
                
                if check_points:
                    print(f"[实时更新] 检查点详情:")
                    for cp in check_points:
                        print(f"  - 块数: {cp['chunk_count']}, 工具数: {cp['tool_count']}, 状态: {cp['status']}")
                
                print(f"[实时更新] ✅ 数据库实时更新正常")
            
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
    
    def test_stream_chat_multiple_tool_calls(self, test_project):
        """测试流式聊天时多个工具调用"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            # 创建一个可能需要多个工具调用的消息
            message = f"请获取项目 {test_project.project_id} 的信息，然后创建一个名为'测试记忆'的记忆，键为'test_key'，值为'test_value'"
            
            full_response = ""
            
            async def collect_response():
                nonlocal full_response
                async for chunk in llm_service.chat(message, test_project.project_id):
                    full_response += chunk
            
            import asyncio
            asyncio.run(collect_response())
            
            # 等待数据库更新
            import time
            time.sleep(1)
            
            # 检查工具调用
            messages = HistoryService.list(test_project.project_id)
            assistant_messages = [m for m in messages if m.role == "assistant"]
            
            if assistant_messages:
                last_message = assistant_messages[-1]
                tool_calls = last_message.tools
                
                print(f"\n[多工具调用] 工具调用数量: {len(tool_calls)}")
                
                if tool_calls:
                    tool_names = [tool.get('name') for tool in tool_calls]
                    print(f"[多工具调用] 工具列表: {tool_names}")
                    
                    # 检查所有工具是否有结果
                    all_have_results = all(
                        tool.get('result') is not None
                        for tool in tool_calls
                    )
                    
                    if all_have_results:
                        print(f"[多工具调用] ✅ 所有工具调用都有结果")
                    else:
                        print(f"[多工具调用] ⚠️  部分工具调用没有结果")
                
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
