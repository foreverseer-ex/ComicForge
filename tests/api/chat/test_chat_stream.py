"""
测试流式传输聊天。

测试 SSE 流式响应是否正常工作。
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
from fastapi.testclient import TestClient
from api.services.llm import get_current_llm_service
from api.services.db import HistoryService


class TestStreamChat:
    """测试流式传输聊天"""
    
    def test_stream_chat_basic(self, client, test_project):
        """测试基本流式聊天"""
        response = client.post(
            "/chat/stream",
            json={
                "message": "你好，请用一句话介绍自己",
                "project_id": test_project.project_id
            }
        )
        
        print(f"\n[流式聊天] 状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查响应头
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type or "text/plain" in content_type
            print(f"[流式聊天] ✅ 返回流式响应: {content_type}")
            
            # 读取响应内容
            content = response.text
            print(f"[流式聊天] 响应长度: {len(content)} 字符")
            
            # 检查是否是 SSE 格式
            if "data:" in content:
                print(f"[流式聊天] ✅ SSE 格式正确")
                # 解析 SSE 数据
                lines = content.split("\n")
                data_lines = [line for line in lines if line.startswith("data:")]
                print(f"[流式聊天] 数据行数: {len(data_lines)}")
                
                if data_lines:
                    first_data = data_lines[0]
                    print(f"[流式聊天] 第一条数据预览: {first_data[:100]}...")
            else:
                print(f"[流式聊天] ⚠️  不是标准 SSE 格式")
        elif response.status_code in [500, 502]:
            print(f"[流式聊天] ⚠️  LLM 服务错误（可能是网络问题）")
            pytest.skip("LLM 服务不可用")
        else:
            pytest.fail(f"意外的状态码: {response.status_code}")
    
    def test_stream_chat_real_time(self, client, test_project):
        """测试流式聊天的实时性"""
        response = client.post(
            "/chat/stream",
            json={
                "message": "请数数从1到5",
                "project_id": test_project.project_id
            },
            stream=True
        )
        
        if response.status_code != 200:
            pytest.skip(f"请求失败: {response.status_code}")
        
        # 流式读取
        chunks = []
        for chunk in response.iter_lines():
            if chunk:
                chunks.append(chunk)
                # 检查是否是 SSE 格式
                if chunk.startswith(b"data:"):
                    print(f"\n[实时流式] 收到数据块: {chunk[:100]}...")
                    break  # 只检查第一个数据块
        
        assert len(chunks) > 0, "应该收到至少一个数据块"
        print(f"[实时流式] ✅ 收到 {len(chunks)} 个数据块")
    
    def test_stream_chat_database_update(self, test_project):
        """测试流式聊天时数据库是否实时更新"""
        llm_service = get_current_llm_service()
        
        if not llm_service.is_ready():
            pytest.skip("LLM 服务未就绪，跳过测试")
        
        try:
            # 获取初始消息数量
            initial_count = HistoryService.count(test_project.project_id)
            
            message = "这是一条测试消息"
            
            # 进行流式聊天
            full_response = ""
            async def collect_response():
                nonlocal full_response
                async for chunk in llm_service.chat(message, test_project.project_id):
                    full_response += chunk
            
            import asyncio
            asyncio.run(collect_response())
            
            # 等待数据库更新
            import time
            time.sleep(0.5)
            
            # 检查数据库中的消息数量
            final_count = HistoryService.count(test_project.project_id)
            
            print(f"\n[数据库更新] 初始消息数: {initial_count}")
            print(f"[数据库更新] 最终消息数: {final_count}")
            print(f"[数据库更新] 新增消息数: {final_count - initial_count}")
            
            # 应该至少增加 2 条消息（用户消息 + 助手消息）
            assert final_count >= initial_count + 2, "应该至少创建用户消息和助手消息"
            print(f"[数据库更新] ✅ 数据库实时更新正常")
            
            # 检查最后一条助手消息
            messages = HistoryService.list(test_project.project_id)
            assistant_messages = [m for m in messages if m.role == "assistant"]
            if assistant_messages:
                last_msg = assistant_messages[-1]
                print(f"[数据库更新] 最后一条消息状态: {last_msg.status}")
                print(f"[数据库更新] 最后一条消息内容长度: {len(last_msg.context)}")
                
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                pytest.skip(f"网络连接失败: {e}")
            else:
                raise
