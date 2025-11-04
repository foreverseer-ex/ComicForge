"""
聊天消息数据库服务。

提供聊天消息的增删改查操作，使用简单的数据库结构。
"""
from typing import Optional, List
from loguru import logger
from sqlmodel import select

from api.services.db.base import DatabaseSession
from api.schemas.desperate.chat_db import ChatMessageDB
from api.schemas.desperate.chat import ChatMessage as ChatMessagePydantic, IterationChatMessage, TextMessage, ToolCall


class ChatService:
    """
    聊天消息数据库服务（单例模式）。
    
    使用类方法提供统一的 CRUD 接口。
    """
    
    @classmethod
    def _chat_message_to_db(cls, msg: ChatMessagePydantic | IterationChatMessage, project_id: str, index: int, status: str = "ready") -> ChatMessageDB:
        """
        将 Pydantic 消息对象转换为数据库模型。
        
        :param msg: 消息对象（ChatMessage 或 IterationChatMessage）
        :param project_id: 项目ID
        :param index: 消息索引
        :param status: 消息状态
        :return: 数据库模型对象
        """
        # 提取文本内容
        message_text = ""
        for content in msg.messages:
            if isinstance(content, TextMessage):
                message_text += content.content + "\n"
        
        # 提取工具调用
        tools_list = []
        for content in msg.messages:
            if isinstance(content, ToolCall):
                tools_list.append({
                    "tool_name": content.tool_name,
                    "arguments": content.arguments,
                    "result": content.result
                })
        
        # 判断消息类型
        message_type = "iteration" if isinstance(msg, IterationChatMessage) else "normal"
        
        # 提取额外数据
        data = {}
        if isinstance(msg, IterationChatMessage):
            data = {
                "target": msg.target,
                "index": msg.index,
                "stop": msg.stop,
                "step": msg.step,
                "summary": msg.summary
            }
        
        return ChatMessageDB(
            project_id=project_id,
            index=index,
            message_id=msg.id,
            status=status,
            message_type=message_type,
            role=msg.role,
            message=message_text.strip(),
            tools=tools_list,
            data=data
        )
    
    @classmethod
    def db_to_chat_message(cls, db_msg: ChatMessageDB) -> ChatMessagePydantic | IterationChatMessage:
        """
        将数据库模型转换为 Pydantic 消息对象。
        
        :param db_msg: 数据库模型对象
        :return: 消息对象（ChatMessage 或 IterationChatMessage）
        """
        # 重建消息内容列表
        messages = []
        if db_msg.message:
            # 解析文本内容（可能包含多行）
            for line in db_msg.message.split("\n"):
                if line.strip():
                    messages.append(TextMessage(content=line.strip()))
        
        # 重建工具调用
        for tool_data in db_msg.tools:
            messages.append(ToolCall(
                tool_name=tool_data.get("tool_name", ""),
                arguments=tool_data.get("arguments", {}),
                result=tool_data.get("result")
            ))
        
        # 根据消息类型创建对象
        if db_msg.message_type == "iteration":
            return IterationChatMessage(
                id=db_msg.message_id,
                role=db_msg.role,
                messages=messages,
                target=db_msg.data.get("target", ""),
                index=db_msg.data.get("index", 0),
                stop=db_msg.data.get("stop", 0),
                step=db_msg.data.get("step", 1),
                summary=db_msg.data.get("summary", "")
            )
        else:
            return ChatMessagePydantic(
                id=db_msg.message_id,
                role=db_msg.role,
                messages=messages
            )
    
    @classmethod
    def add(cls, project_id: str, message: ChatMessagePydantic | IterationChatMessage, status: str = "ready") -> ChatMessageDB:
        """
        添加消息到数据库。
        
        如果消息已存在（通过 message_id），则更新它而不是创建新记录。
        
        :param project_id: 项目ID
        :param message: 消息对象
        :param status: 消息状态（默认"ready"）
        :return: 创建的数据库记录
        """
        with DatabaseSession() as db:
            # 检查消息是否已存在
            statement = select(ChatMessageDB).where(
                ChatMessageDB.project_id == project_id,
                ChatMessageDB.message_id == message.id
            )
            existing_msg = db.exec(statement).first()
            
            if existing_msg:
                # 消息已存在，更新它
                from datetime import datetime
                new_db_msg = cls._chat_message_to_db(message, project_id, existing_msg.index, status)
                existing_msg.status = new_db_msg.status
                existing_msg.message_type = new_db_msg.message_type
                existing_msg.role = new_db_msg.role
                existing_msg.message = new_db_msg.message
                existing_msg.tools = new_db_msg.tools
                existing_msg.data = new_db_msg.data
                existing_msg.updated_at = datetime.now()
                
                db.add(existing_msg)
                db.flush()
                db.refresh(existing_msg)
                db.expunge(existing_msg)
                logger.debug(f"更新已存在的消息: {project_id}, message_id={message.id}, status={status}")
                return existing_msg
            
            # 消息不存在，创建新记录
            # 获取当前会话的最大索引
            statement = select(ChatMessageDB).where(
                ChatMessageDB.project_id == project_id
            ).order_by(ChatMessageDB.index.desc()).limit(1)
            last_msg = db.exec(statement).first()
            next_index = (last_msg.index + 1) if last_msg else 0
            
            # 创建数据库记录
            db_msg = cls._chat_message_to_db(message, project_id, next_index, status)
            db.add(db_msg)
            db.flush()
            db.refresh(db_msg)
            db.expunge(db_msg)
            logger.debug(f"添加消息到数据库: {project_id}, index={next_index}, message_id={message.id}, status={status}")
            return db_msg
    
    @classmethod
    def update(cls, project_id: str, message_id: str, message: ChatMessagePydantic | IterationChatMessage, status: Optional[str] = None) -> Optional[ChatMessageDB]:
        """
        更新消息。
        
        :param project_id: 项目ID
        :param message_id: 消息ID
        :param message: 新的消息对象
        :param status: 新的状态（可选，如果不提供则保持不变）
        :return: 更新后的数据库记录，如果不存在则返回None
        """
        with DatabaseSession() as db:
            statement = select(ChatMessageDB).where(
                ChatMessageDB.project_id == project_id,
                ChatMessageDB.message_id == message_id
            )
            db_msg = db.exec(statement).first()
            
            if not db_msg:
                logger.warning(f"消息不存在，无法更新: {project_id}, {message_id}")
                return None
            
            # 更新字段
            from datetime import datetime
            new_db_msg = cls._chat_message_to_db(message, project_id, db_msg.index, status or db_msg.status)
            db_msg.status = new_db_msg.status
            db_msg.message_type = new_db_msg.message_type
            db_msg.role = new_db_msg.role
            db_msg.message = new_db_msg.message
            db_msg.tools = new_db_msg.tools
            db_msg.data = new_db_msg.data
            db_msg.updated_at = datetime.now()
            
            db.add(db_msg)
            db.flush()
            db.refresh(db_msg)
            db.expunge(db_msg)
            logger.debug(f"更新消息: {project_id}, message_id={message_id}, status={db_msg.status}")
            return db_msg
    
    @classmethod
    def update_status(cls, project_id: str, message_id: str, status: str) -> bool:
        """
        只更新消息状态（用于快速更新状态）。
        
        :param project_id: 项目ID
        :param message_id: 消息ID
        :param status: 新状态
        :return: 是否更新成功
        """
        with DatabaseSession() as db:
            statement = select(ChatMessageDB).where(
                ChatMessageDB.project_id == project_id,
                ChatMessageDB.message_id == message_id
            )
            db_msg = db.exec(statement).first()
            
            if not db_msg:
                logger.warning(f"消息不存在，无法更新状态: {project_id}, {message_id}")
                return False
            
            db_msg.status = status
            db.add(db_msg)
            logger.debug(f"更新消息状态: {project_id}, message_id={message_id}, status={status}")
            return True
    
    @classmethod
    def list(cls, project_id: str, start: int = 0, end: Optional[int] = None) -> List[ChatMessageDB]:
        """
        获取会话的所有消息。
        
        :param project_id: 项目ID
        :param start: 起始索引
        :param end: 结束索引（None表示到末尾）
        :return: 消息列表
        """
        with DatabaseSession() as db:
            statement = select(ChatMessageDB).where(
                ChatMessageDB.project_id == project_id
            ).order_by(ChatMessageDB.index)
            
            if start > 0:
                statement = statement.offset(start)
            if end is not None:
                statement = statement.limit(end - start)
            
            messages = db.exec(statement).all()
            # 分离所有对象
            for msg in messages:
                db.expunge(msg)
            return list(messages)
    
    @classmethod
    def get_by_message_id(cls, project_id: str, message_id: str) -> Optional[ChatMessageDB]:
        """
        根据消息ID获取消息。
        
        :param project_id: 项目ID
        :param message_id: 消息ID
        :return: 消息对象，如果不存在则返回None
        """
        with DatabaseSession() as db:
            statement = select(ChatMessageDB).where(
                ChatMessageDB.project_id == project_id,
                ChatMessageDB.message_id == message_id
            )
            db_msg = db.exec(statement).first()
            if db_msg:
                db.expunge(db_msg)
            return db_msg
    
    @classmethod
    def get_last(cls, project_id: str) -> Optional[ChatMessageDB]:
        """
        获取会话的最后一条消息。
        
        :param project_id: 项目ID
        :return: 最后一条消息，如果不存在则返回None
        """
        with DatabaseSession() as db:
            statement = select(ChatMessageDB).where(
                ChatMessageDB.project_id == project_id
            ).order_by(ChatMessageDB.index.desc()).limit(1)
            db_msg = db.exec(statement).first()
            if db_msg:
                db.expunge(db_msg)
            return db_msg
    
    @classmethod
    def delete(cls, project_id: str, message_id: str) -> bool:
        """
        删除消息。
        
        :param project_id: 项目ID
        :param message_id: 消息ID
        :return: 是否删除成功
        """
        with DatabaseSession() as db:
            statement = select(ChatMessageDB).where(
                ChatMessageDB.project_id == project_id,
                ChatMessageDB.message_id == message_id
            )
            db_msg = db.exec(statement).first()
            
            if not db_msg:
                logger.warning(f"消息不存在，无法删除: {project_id}, {message_id}")
                return False
            
            db.delete(db_msg)
            logger.debug(f"删除消息: {project_id}, message_id={message_id}")
            return True
    
    @classmethod
    def clear(cls, project_id: str) -> int:
        """
        清空会话的所有消息。
        
        :param project_id: 项目ID
        :return: 删除的消息数量
        """
        with DatabaseSession() as db:
            statement = select(ChatMessageDB).where(
                ChatMessageDB.project_id == project_id
            )
            messages = db.exec(statement).all()
            count = len(messages)
            
            for msg in messages:
                db.delete(msg)
            
            logger.info(f"清空会话消息: {project_id}, 共 {count} 条")
            return count
    
    @classmethod
    def get_message_ids(cls, project_id: str) -> List[str]:
        """
        获取会话的所有消息ID列表（用于前端对比）。
        
        :param project_id: 项目ID
        :return: 消息ID列表（按index排序）
        """
        with DatabaseSession() as db:
            statement = select(ChatMessageDB.message_id).where(
                ChatMessageDB.project_id == project_id
            ).order_by(ChatMessageDB.index)
            message_ids = db.exec(statement).all()
            return list(message_ids)

