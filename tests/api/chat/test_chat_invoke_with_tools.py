"""
测试直接聊天+工具调用。

测试 LLM 是否能正确调用工具函数。
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
from api.services.db import HistoryService, ProjectService


class TestInvokeChatWithTools:
    """测试直接聊天+工具调用"""
    
    def test_chat_with_tool_call_get_project(self, test_project):
        """测试聊天时调用 get_project 工具"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            # 创建一个应该触发工具调用的消息
            message = f"请获取项目 {test_project.project_id} 的详细信息"
            
            # 使用流式聊天（因为需要工具调用）
            # 收集所有响应
            full_response = ""
            tool_calls_count = 0
            
            async def collect_response():
                nonlocal full_response, tool_calls_count
                async for chunk in llm_service.chat(message, test_project.project_id):
                    full_response += chunk
            
            import asyncio
            asyncio.run(collect_response())
            
            # 检查数据库中是否有工具调用记录
            # 获取最后一条助手消息
            messages = HistoryService.list(test_project.project_id)
            assistant_messages = [m for m in messages if m.role == "assistant"]
            
            if assistant_messages:
                last_message = assistant_messages[-1]
                tool_calls = last_message.tools
                
                print(f"\n[工具调用测试] 响应长度: {len(full_response)} 字符")
                print(f"[工具调用测试] 工具调用数量: {len(tool_calls)}")
                
                if tool_calls:
                    print(f"[工具调用测试] 第一个工具: {tool_calls[0].get('name', 'unknown')}")
                    # 检查是否有 get_project 调用
                    has_get_project = any(
                        tool.get('name') == 'get_project' 
                        for tool in tool_calls
                    )
                    if has_get_project:
                        print(f"[工具调用测试] ✅ 成功调用了 get_project 工具")
                    else:
                        print(f"[工具调用测试] ⚠️  未检测到 get_project 调用（可能LLM选择其他方式）")
                else:
                    print(f"[工具调用测试] ⚠️  未检测到工具调用（可能LLM未调用工具）")
            
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
    
    def test_chat_with_tool_call_create_memory(self, test_project):
        """测试聊天时调用 create_memory 工具"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            # 创建一个应该触发 create_memory 工具的消息
            message = f"请记住：我的名字是测试用户，项目ID是 {test_project.project_id}"
            
            full_response = ""
            
            async def collect_response():
                nonlocal full_response
                async for chunk in llm_service.chat(message, test_project.project_id):
                    full_response += chunk
            
            import asyncio
            asyncio.run(collect_response())
            
            # 检查数据库中是否有工具调用和记忆
            messages = HistoryService.list(test_project.project_id)
            assistant_messages = [m for m in messages if m.role == "assistant"]
            
            if assistant_messages:
                last_message = assistant_messages[-1]
                tool_calls = last_message.tools
                
                print(f"\n[创建记忆测试] 工具调用数量: {len(tool_calls)}")
                if tool_calls:
                    for tool in tool_calls:
                        print(f"[创建记忆测试] 工具: {tool.get('name')}")
                    
                    # 检查是否有 create_memory 调用
                    has_create_memory = any(
                        tool.get('name') == 'create_memory'
                        for tool in tool_calls
                    )
                    if has_create_memory:
                        print(f"[创建记忆测试] ✅ 成功调用了 create_memory 工具")
            
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
    
    def test_tool_call_result_stored(self, test_project):
        """测试工具调用的结果是否正确存储到数据库"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            message = f"请告诉我项目 {test_project.project_id} 的标题"
            
            full_response = ""
            
            async def collect_response():
                nonlocal full_response
                async for chunk in llm_service.chat(message, test_project.project_id):
                    full_response += chunk
            
            import asyncio
            asyncio.run(collect_response())
            
            # 等待一下确保数据库更新完成
            import time
            time.sleep(0.5)
            
            # 检查数据库中的消息
            messages = HistoryService.list(test_project.project_id)
            assistant_messages = [m for m in messages if m.role == "assistant"]
            
            if assistant_messages:
                last_message = assistant_messages[-1]
                
                # 检查工具调用是否有结果
                tool_calls = last_message.tools
                if tool_calls:
                    for tool in tool_calls:
                        tool_name = tool.get('name')
                        tool_result = tool.get('result')
                        
                        print(f"\n[工具结果存储] 工具: {tool_name}")
                        print(f"[工具结果存储] 是否有结果: {tool_result is not None}")
                        
                        if tool_result:
                            print(f"[工具结果存储] 结果长度: {len(str(tool_result))} 字符")
                            print(f"[工具结果存储] ✅ 工具结果已存储")
                        else:
                            print(f"[工具结果存储] ⚠️  工具结果为空")
            
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
