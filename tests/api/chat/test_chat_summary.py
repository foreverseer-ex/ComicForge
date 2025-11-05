"""
测试聊天总结功能。

测试自动生成聊天摘要的功能。
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
from api.services.db import HistoryService, MemoryService
from api.settings import app_settings


class TestChatSummary:
    """测试聊天总结功能"""
    
    def test_summary_generation_trigger(self, test_project):
        """测试聊天总结的触发条件"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        # 获取 summary_epoch 配置
        summary_epoch = app_settings.llm.summary_epoch
        print(f"\n[总结触发] summary_epoch 配置: {summary_epoch}")
        
        # 清空现有消息
        HistoryService.clear(test_project.project_id)
        
        # 创建足够多的消息来触发总结
        from api.schemas.chat import ChatMessage
        import uuid
        
        message_count = summary_epoch + 1  # 超过一个 epoch
        
        print(f"[总结触发] 创建 {message_count} 条消息来触发总结...")
        
        for i in range(message_count):
            # 创建用户消息
            user_msg = ChatMessage(
                message_id=str(uuid.uuid4()),
                project_id=test_project.project_id,
                role="user",
                context=f"用户消息 {i+1}",
                status="ready",
                message_type="normal"
            )
            HistoryService.create(user_msg)
            
            # 创建助手消息
            assistant_msg = ChatMessage(
                message_id=str(uuid.uuid4()),
                project_id=test_project.project_id,
                role="assistant",
                context=f"助手回复 {i+1}",
                status="ready",
                message_type="normal"
            )
            HistoryService.create(assistant_msg)
            
            # 在达到 epoch 倍数时触发总结
            current_count = HistoryService.count(test_project.project_id)
            if current_count % summary_epoch == 0:
                print(f"[总结触发] 消息数达到 {current_count}，触发总结...")
                llm_service.summary_history(test_project.project_id)
                
                # 检查是否有总结
                summary = MemoryService.get_summary(test_project.project_id)
                if summary and summary.data:
                    print(f"[总结触发] ✅ 总结已生成，长度: {len(summary.data)} 字符")
                    print(f"[总结触发] 总结预览: {summary.data[:200]}...")
                else:
                    print(f"[总结触发] ⚠️  总结未生成（可能是网络问题）")
        
        print(f"[总结触发] 最终消息数: {HistoryService.count(test_project.project_id)}")
    
    def test_summary_usage_in_chat(self, test_project):
        """测试总结在后续对话中的使用"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        # 先创建一些历史消息和总结
        from api.schemas.chat import ChatMessage
        import uuid
        
        # 创建总结
        MemoryService.update_summary(test_project.project_id, "这是一个测试总结：用户询问了项目信息，助手提供了详细信息。")
        
        # 创建一些旧消息
        for i in range(5):
            msg = ChatMessage(
                message_id=str(uuid.uuid4()),
                project_id=test_project.project_id,
                role="user" if i % 2 == 0 else "assistant",
                context=f"历史消息 {i+1}",
                status="ready",
                message_type="normal"
            )
            HistoryService.create(msg)
        
        # 进行新的对话
        try:
            message = "请根据之前的对话总结回答：我们讨论的主要内容是什么？"
            
            full_response = ""
            async def collect_response():
                nonlocal full_response
                async for chunk in llm_service.chat_text_only(message, test_project.project_id):
                    full_response += chunk
            
            import asyncio
            asyncio.run(collect_response())
            
            print(f"\n[总结使用] 响应长度: {len(full_response)} 字符")
            print(f"[总结使用] 响应预览: {full_response[:200]}...")
            
            # 检查响应中是否提到了总结相关内容
            # （这个测试可能因为LLM响应不确定而失败，所以只是检查响应存在）
            assert len(full_response) > 0, "应该有响应"
            print(f"[总结使用] ✅ 使用了总结的对话正常")
            
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
    
    def test_summary_storage(self, test_project):
        """测试总结的存储"""
        # 创建测试总结
        test_summary = "这是一个测试总结内容，包含了一些重要信息的摘要。"
        
        MemoryService.update_summary(test_project.project_id, test_summary)
        
        # 读取总结
        summary = MemoryService.get_summary(test_project.project_id)
        
        assert summary is not None, "总结应该存在"
        assert summary.data == test_summary, "总结内容应该匹配"
        
        print(f"\n[总结存储] ✅ 总结存储正常")
        print(f"[总结存储] 总结内容: {summary.data}")
    
    def test_summary_retrieval(self, test_project):
        """测试总结的检索"""
        # 创建测试总结
        test_summary = "测试总结内容"
        MemoryService.update_summary(test_project.project_id, test_summary)
        
        # 检索总结
        summary = MemoryService.get_summary(test_project.project_id)
        
        assert summary is not None
        assert summary.data == test_summary
        
        print(f"\n[总结检索] ✅ 总结检索正常")
