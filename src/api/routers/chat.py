"""
聊天对话路由。

提供 AI 对话相关的 API 端点：
- 直接对话（invoke模式）- 非流式，直接返回完整结果
- 流式对话（stream模式）- SSE 流式返回
- 迭代式对话 - 用于处理大量内容的迭代式对话
"""
import asyncio
import json
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from api.schemas.chat import ChatIteration
from api.services.llm import get_current_llm_service
from api.services.db import HistoryService

router = APIRouter(
    prefix="/chat",
    tags=["AI 对话"],
    responses={404: {"description": "资源不存在"}},
)


class ChatRequest(BaseModel):
    """对话请求（用于 invoke 和 stream 模式）"""
    message: str = Field(description="用户消息")
    project_id: str = Field(description="项目ID")


class IterationRequest(BaseModel):
    """迭代式对话请求"""
    project_id: str = Field(description="项目ID")
    target: str = Field(description="迭代目标")
    index: int = Field(description="起始索引", default=0)
    stop: int = Field(description="终止索引")
    step: int = Field(description="步长", default=100)
    summary: str = Field(description="摘要", default="")
    message_id: str | None = Field(description="消息ID（如果继续现有迭代）", default=None)


@router.post("/invoke", summary="直接对话（invoke模式）")
async def chat_invoke(request: ChatRequest):
    """
    直接对话端点（invoke模式）- 非流式，直接返回完整结果。
    
    支持：
    - 直接返回完整 LLM 响应（非流式）
    - 工具调用保存到数据库
    - 建议自动添加到数据库
    - 消息保存到历史记录
    
    Args:
        request: 包含 message 和 project_id 的请求体
    
    Returns:
        JSON 响应，包含：
        - message_id: 助手消息ID
        - content: 完整响应内容
        - tools: 工具调用列表
        - suggests: 建议列表
        - status: 消息状态
    """
    llm_service = get_current_llm_service()
    
    if not llm_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail="LLM 服务未就绪，请先初始化 LLM"
        )
    
    try:
        # 收集完整响应
        full_response = ""
        async for chunk in llm_service.chat_text_only(request.message, request.project_id):
            full_response += chunk
        
        # 等待数据库更新完成
        await asyncio.sleep(0.1)
        
        # 获取最后一条助手消息（包含工具调用和建议）
        messages = HistoryService.list(request.project_id)
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        if assistant_messages:
            last_message = assistant_messages[-1]
            return {
                "message_id": last_message.message_id,
                "content": full_response,
                "tools": last_message.tools,
                "suggests": last_message.suggests,
                "status": last_message.status
            }
        else:
            # 如果没有找到助手消息，返回响应内容
            return {
                "message_id": None,
                "content": full_response,
                "tools": [],
                "suggests": [],
                "status": "ready"
            }
            
    except Exception as e:
        logger.exception(f"直接对话失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"对话失败: {str(e)}"
        )


@router.post("/stream", summary="流式对话")
async def chat_stream(request: ChatRequest):
    """
    标准流式对话端点。
    
    支持：
    - 流式返回 LLM 响应
    - 工具调用实时通知前端
    - 建议实时通知前端
    - 消息状态更新
    
    Args:
        request: 包含 message 和 project_id 的请求体
    
    Returns:
        SSE 流式响应（text/event-stream）
        
    事件类型：
    - content: 文本内容片段
    - tool_start: 工具调用开始 {name, args}
    - tool_end: 工具调用结束 {name, result}
    - suggest: 建议更新 {suggests: [...]}
    - message_id: 消息ID {message_id: "..."}
    - status: 消息状态 {status: "thinking|ready|error"}
    - done: 完成标志 {}
    - error: 错误信息 {error: "..."}
    """
    llm_service = get_current_llm_service()
    
    if not llm_service.is_ready():
        async def error_generate():
            error_data = json.dumps({
                'type': 'error',
                'error': 'LLM 服务未就绪，请先初始化 LLM'
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            error_generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    async def generate():
        try:
            assistant_message_id = None
            last_tools = []
            last_suggests = []
            
            # 使用改进的流式生成器，它会yield不同的事件类型
            async for event in llm_service.chat_streamed(request.message, request.project_id):
                event_type = event.get('type')
                
                if event_type == 'content':
                    # 文本内容
                    yield f"data: {json.dumps({'type': 'content', 'content': event.get('content', '')}, ensure_ascii=False)}\n\n"
                
                elif event_type == 'message_id':
                    # 消息ID
                    assistant_message_id = event.get('message_id')
                    yield f"data: {json.dumps({'type': 'message_id', 'message_id': assistant_message_id}, ensure_ascii=False)}\n\n"
                
                elif event_type == 'tool_start':
                    # 工具调用开始
                    tool_info = {
                        'type': 'tool_start',
                        'name': event.get('name', ''),
                        'args': event.get('args', {})
                    }
                    yield f"data: {json.dumps(tool_info, ensure_ascii=False)}\n\n"
                
                elif event_type == 'tool_end':
                    # 工具调用结束
                    tool_info = {
                        'type': 'tool_end',
                        'name': event.get('name', ''),
                        'result': event.get('result')
                    }
                    yield f"data: {json.dumps(tool_info, ensure_ascii=False)}\n\n"
                
                elif event_type == 'tools':
                    # 工具调用列表更新
                    tools = event.get('tools', [])
                    if tools != last_tools:
                        last_tools = tools
                        yield f"data: {json.dumps({'type': 'tools', 'tools': tools}, ensure_ascii=False)}\n\n"
                
                elif event_type == 'suggests':
                    # 建议更新
                    suggests = event.get('suggests', [])
                    if suggests != last_suggests:
                        last_suggests = suggests
                        yield f"data: {json.dumps({'type': 'suggests', 'suggests': suggests}, ensure_ascii=False)}\n\n"
                
                elif event_type == 'status':
                    # 状态更新
                    yield f"data: {json.dumps({'type': 'status', 'status': event.get('status', 'ready')}, ensure_ascii=False)}\n\n"
            
            # 发送完成标志
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.exception(f"流式对话失败: {e}")
            error_data = json.dumps({
                'type': 'error',
                'error': str(e)
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/iteration", summary="迭代式对话")
async def chat_iteration(request: IterationRequest):
    """
    迭代式对话端点。
    
    支持：
    - 迭代式处理大量内容
    - 实时更新迭代进度到数据库
    - 最终操作的工具调用记录
    
    Args:
        request: 迭代请求，包含：
            - project_id: 项目ID
            - target: 迭代目标
            - index: 起始索引
            - stop: 终止索引
            - step: 步长
            - summary: 摘要（可选）
            - message_id: 消息ID（如果继续现有迭代）
    
    Returns:
        SSE 流式响应（text/event-stream）
    """
    # 构建迭代数据字典
    iteration_data = {
        "target": request.target,
        "index": request.index,
        "stop": request.stop,
        "step": request.step,
        "summary": request.summary
    }
    if request.message_id:
        iteration_data["message_id"] = request.message_id
    
    llm_service = get_current_llm_service()
    
    async def generate():
        try:
            async for chunk in llm_service.chat_iteration(iteration_data, request.project_id):
                # SSE 格式：data: {content}\n\n
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.exception(f"迭代对话失败: {e}")
            error_data = json.dumps({'error': str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/status/{message_id}", summary="获取消息状态")
async def get_message_status(
    message_id: str,
    project_id: str
):
    """
    获取消息的当前状态（用于前端轮询）。
    
    Args:
        message_id: 消息ID
        project_id: 项目ID
    
    Returns:
        消息状态信息
    """
    message = HistoryService.get(message_id)
    if not message or message.project_id != project_id:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    return {
        "message_id": message.message_id,
        "status": message.status,
        "context": message.context,
        "tools": message.tools,
        "suggests": message.suggests,
        "data": message.data if message.message_type == "iteration" else None
    }

