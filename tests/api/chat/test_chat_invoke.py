"""
测试直接聊天（invoke模式）- 非流式，直接返回结果。
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


class TestInvokeChat:
    """测试直接聊天（invoke模式）"""
    
    def test_simple_chat_basic(self, test_project):
        """测试基本直接聊天"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            # 使用 simple_chat 方法（非流式）
            response = llm_service.simple_chat("你好，请简单介绍一下自己")
            
            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
            
            print(f"\n[直接聊天] 响应长度: {len(response)} 字符")
            print(f"[直接聊天] 响应预览: {response[:100]}...")
            
        except Exception as e:
            # 网络错误等可以接受，但服务应该正常
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败（这是正常的）: {e}")
            else:
                raise
    
    def test_simple_chat_with_context(self, test_project):
        """测试带上下文的直接聊天"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            # 先创建一条用户消息
            from api.schemas.chat import ChatMessage
            import uuid
            
            user_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                project_id=test_project.project_id,
                role="user",
                context="我的项目名称是：测试项目",
                status="ready",
                message_type="normal"
            )
            HistoryService.create(user_message)
            
            # 然后进行对话
            response = llm_service.simple_chat("请记住我的项目名称")
            
            assert response is not None
            assert isinstance(response, str)
            
            print(f"\n[带上下文聊天] 响应: {response[:150]}...")
            
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
    
    def test_simple_chat_error_handling(self, test_project):
        """测试错误处理"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            # 测试未就绪时的错误处理
            response = llm_service.simple_chat("测试消息")
            assert "错误" in response or "未就绪" in response
            print(f"\n[错误处理] 未就绪响应: {response}")
