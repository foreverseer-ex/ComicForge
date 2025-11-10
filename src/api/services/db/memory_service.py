"""
记忆（Memory）数据库服务。

提供记忆条目和章节摘要的增删改查操作。
"""
from typing import Optional
from loguru import logger
from sqlmodel import select

from .base import DatabaseSession, normalize_project_id
from api.schemas.memory import MemoryEntry, ChatSummary


class MemoryService:
    """
    记忆数据库服务（单例模式）。
    
    使用类方法提供统一的 CRUD 接口。
    """

    # ========== MemoryEntry 操作 ==========

    @classmethod
    def create(cls, entry: MemoryEntry) -> MemoryEntry:
        """
        创建记忆条目。
        
        :param entry: 记忆条目对象
        :return: 创建后的记忆条目对象
        """
        with DatabaseSession() as db:
            db.add(entry)
            db.flush()
            db.refresh(entry)
            db.expunge(entry)
            logger.info(f"创建记忆条目: {entry.key}")
            return entry

    @classmethod
    def get(cls, memory_id: str) -> Optional[MemoryEntry]:
        """
        根据 memory_id 获取记忆条目。
        
        :param memory_id: 记忆ID
        :return: 记忆条目对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            entry = db.get(MemoryEntry, memory_id)
            if entry:
                db.expunge(entry)
                logger.debug(f"获取记忆条目: {memory_id}")
            else:
                logger.warning(f"记忆条目不存在: {memory_id}")
            return entry

    @classmethod
    def get_all(cls, project_id: Optional[str], limit: Optional[int] = None, offset: int = 0) -> list[MemoryEntry]:
        """
        根据会话 ID 获取记忆条目列表。
        
        :param project_id: 会话 ID（None 表示默认工作空间）
        :param limit: 返回数量限制（None 表示无限制）
        :param offset: 跳过的记录数
        :return: 记忆条目列表
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            # 如果 project_id 为 None，查询 project_id 为 None 的记录
            if project_id is None:
                statement = select(MemoryEntry).where(MemoryEntry.project_id.is_(None)).offset(offset)
            else:
                statement = select(MemoryEntry).where(MemoryEntry.project_id == project_id).offset(offset)
            if limit is not None:
                statement = statement.limit(limit)

            entries = db.exec(statement).all()
            for entry in entries:
                db.expunge(entry)
            logger.debug(f"获取会话 {project_id} 的记忆条目: {len(entries)} 条")
            return list(entries)

    @classmethod
    def update(cls, memory_id: str, **kwargs) -> Optional[MemoryEntry]:
        """
        更新记忆条目。
        
        :param memory_id: 记忆ID
        :param kwargs: 要更新的字段
        :return: 更新后的记忆条目对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            entry = db.get(MemoryEntry, memory_id)
            if not entry:
                logger.warning(f"记忆条目不存在，无法更新: {memory_id}")
                return None

            # 更新字段
            for field, value in kwargs.items():
                if hasattr(entry, field):
                    setattr(entry, field, value)

            db.add(entry)
            db.flush()
            db.refresh(entry)
            db.expunge(entry)
            logger.info(f"更新记忆条目: {memory_id}")
            return entry

    @classmethod
    def remove(cls, memory_id: str) -> bool:
        """
        删除记忆条目。
        
        :param memory_id: 记忆ID
        :return: 是否删除成功
        """
        with DatabaseSession() as db:
            entry = db.get(MemoryEntry, memory_id)
            if not entry:
                logger.warning(f"记忆条目不存在，无法删除: {memory_id}")
                return False

            db.delete(entry)
            logger.info(f"删除记忆条目: {memory_id}")
            return True

    @classmethod
    def clear(cls, project_id: Optional[str]) -> int:
        """
        删除指定会话的所有记忆条目。
        
        :param project_id: 项目ID（None 表示默认工作空间）
        :return: 删除的记录数
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            # 如果 project_id 为 None，查询 project_id 为 None 的记录
            if project_id is None:
                statement = select(MemoryEntry).where(MemoryEntry.project_id.is_(None))
            else:
                statement = select(MemoryEntry).where(MemoryEntry.project_id == project_id)
            entries = db.exec(statement).all()

            count = len(entries)
            for entry in entries:
                db.delete(entry)

            logger.info(f"删除会话 {project_id} 的所有记忆条目: {count} 条")
            return count

    @classmethod
    def get_summary(cls, project_id: str) -> Optional[ChatSummary]:
        """
        根据项目ID获取聊天摘要。

        :param project_id: 项目ID
        :return: 聊天摘要对象，如果不存在则返回 None
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            summary = db.get(ChatSummary, project_id)
            if summary:
                db.expunge(summary)
                logger.debug(f"获取聊天摘要: {project_id}")
            else:
                logger.warning(f"聊天摘要不存在: {project_id}")
            return summary

    @classmethod
    def update_summary(cls, project_id: str, summary: str) -> ChatSummary:
        """
        创建或更新聊天摘要。

        :param project_id: 项目ID
        :param summary: 聊天摘要内容
        :return: 创建或更新后的聊天摘要对象
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            existing = db.get(ChatSummary, project_id)
            if existing:
                existing.data = summary
                db.add(existing)
                logger.info(f"更新聊天摘要: {project_id}")
            else:
                new_summary = ChatSummary(project_id=project_id, data=summary)
                db.add(new_summary)
                logger.info(f"创建聊天摘要: {project_id}")
            db.flush()
            db.refresh(existing or new_summary)
            db.expunge(existing or new_summary)
            return existing or new_summary
