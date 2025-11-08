from typing import Optional, Sequence

from loguru import logger
from sqlalchemy import func
from sqlmodel import select

from api.schemas import ChatMessage
from api.services.db import DatabaseSession


class HistoryService:
    @classmethod
    def create(cls, message: ChatMessage):
        """
        添加聊天消息。

        :param message: 要添加的聊天消息对象
        :return: 添加后的聊天消息对象
        """
        if message.index == -1:
            count = cls.count(message.project_id)
            message.index = count + message.index + 1

        with DatabaseSession() as db:
            db.add(message)
            db.flush()
            db.refresh(message)
            db.expunge(message)
            return message

    @classmethod
    def get(cls, message_id: str) -> Optional[ChatMessage]:
        """
        根据消息ID获取聊天消息。

        :param message_id: 要获取的聊天消息ID
        :return: 聊天消息对象（如果存在）
        """
        with DatabaseSession() as db:
            message = db.exec(
                select(ChatMessage)
                .where(ChatMessage.message_id == message_id)
            ).first()
            if message:
                db.expunge(message)
            return message

    @classmethod
    def get_by_index(cls, project_id: Optional[str], index: int) -> Optional[ChatMessage]:
        """
        根据项目ID和索引获取聊天消息。
        
        :param project_id: 会话唯一标识（None 表示默认工作空间）
        :param index: 消息索引
        :return: 聊天消息对象（如果存在）
        """
        with DatabaseSession() as db:
            statement = select(ChatMessage).where(ChatMessage.index == index)
            if project_id is None:
                statement = statement.where(ChatMessage.project_id.is_(None))
            else:
                statement = statement.where(ChatMessage.project_id == project_id)
            message = db.exec(statement).first()
            if message:
                db.expunge(message)
            return message

    @classmethod
    def get_all(cls, project_id: Optional[str], start_index: int = 0, end_index: int = -1) -> list[ChatMessage]:
        """
        根据项目ID获取聊天消息列表。
        
        :param project_id: 会话唯一标识（None 表示默认工作空间）
        :param start_index: 起始索引，默认值为0
        :param end_index: 结束索引，默认值为-1（表示最后一条消息）
        :return: 聊天消息对象列表（按索引排序）
        """

        if end_index < 0:
            end_index = cls.count(project_id) + end_index


        with DatabaseSession() as db:
            statement = select(ChatMessage).where(ChatMessage.index >= start_index).where(ChatMessage.index <= end_index)
            if project_id is None:
                statement = statement.where(ChatMessage.project_id.is_(None))
            else:
                statement = statement.where(ChatMessage.project_id == project_id)
            statement = statement.order_by(ChatMessage.index)
            messages = db.exec(statement).all()
            for message in messages:
                db.expunge(message)
        return list(messages)

    @classmethod
    def list_ids(cls, project_id: Optional[str]) -> Sequence[str]:
        """
        根据项目ID获取聊天消息ID列表。
        
        :param project_id: 会话唯一标识（None 表示默认工作空间）
        :return: 聊天消息ID列表
        """
        with DatabaseSession() as db:
            statement = select(ChatMessage.message_id)
            if project_id is None:
                statement = statement.where(ChatMessage.project_id.is_(None))
            else:
                statement = statement.where(ChatMessage.project_id == project_id)
            message_ids = db.exec(statement).all()
            return [message_id for message_id, in message_ids]

    @classmethod
    def remove(cls, message_id: str):
        """
        根据消息ID删除聊天消息。

        :param message_id: 要删除的聊天消息ID
        :return: None
        """
        with DatabaseSession() as db:
            message = db.exec(
                select(ChatMessage)
                .where(ChatMessage.message_id == message_id)
            ).first()
            if message:
                db.delete(message)
                logger.info(f"删除聊天消息: {message_id}")

    @classmethod
    def count(cls, project_id: Optional[str]) -> int:
        """
        根据项目ID获取聊天消息数量。
        
        :param project_id: 会话唯一标识（None 表示默认工作空间）
        :return: 聊天消息数量
        """
        with DatabaseSession() as db:
            statement = select(func.count(ChatMessage.index))
            if project_id is None:
                statement = statement.where(ChatMessage.project_id.is_(None))
            else:
                statement = statement.where(ChatMessage.project_id == project_id)
            count = db.exec(statement).first()
            return count

    @classmethod
    def remove_by_index(cls, project_id: Optional[str], index: int = -1):
        """
        根据项目ID和索引删除聊天消息。
        
        :param project_id: 会话唯一标识（None 表示默认工作空间）
        :param index: 消息索引
        :return: None
        """
        if index < 0:
            index = cls.count(project_id) + index
        message = cls.get_by_index(project_id, index)
        if message:
            cls.remove(message.message_id)

    @classmethod
    def clear(cls, project_id: Optional[str]) -> int:
        """
        根据项目ID删除所有聊天消息。
        
        :param project_id: 会话唯一标识（None 表示默认工作空间）
        :return: 删除的记录数
        """
        with DatabaseSession() as db:
            statement = select(ChatMessage)
            if project_id is None:
                statement = statement.where(ChatMessage.project_id.is_(None))
            else:
                statement = statement.where(ChatMessage.project_id == project_id)
            messages = db.exec(statement).all()
            count = len(messages)
            for message in messages:
                db.delete(message)
            logger.info(f"删除项目 {project_id} 的所有聊天消息: {count} 条")
            return count

    @classmethod
    def update(cls, message: ChatMessage):
        """
        更新聊天消息。

        :param message: 要更新的聊天消息对象
        :return: 更新后的聊天消息对象
        """
        with DatabaseSession() as db:
            db.add(message)
            db.flush()
            db.refresh(message)
            db.expunge(message)
            return message


chat_service = HistoryService()
