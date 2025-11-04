"""
记忆（Memory）数据库服务。

提供记忆条目和章节摘要的增删改查操作。
"""
from typing import Optional

from loguru import logger
from sqlmodel import select

from api.schemas.memory import ChapterSummary
from .base import DatabaseSession


class SummaryService:
    """
    章节摘要数据库服务（单例模式）。

    使用类方法提供统一的 CRUD 接口。
    """

    @classmethod
    def create(cls, summary: ChapterSummary) -> ChapterSummary:
        """
        创建章节摘要。

        :param summary: 章节摘要对象
        :return: 创建后的章节摘要对象
        """
        with DatabaseSession() as db:
            db.add(summary)
            db.flush()
            db.refresh(summary)
            db.expunge(summary)
            logger.info(f"创建章节摘要: chapter {summary.chapter_index}")
            return summary

    @classmethod
    def get(cls, project_id: str, chapter_index: int) -> Optional[ChapterSummary]:
        """
        根据项目ID和章节索引获取摘要。

        :param project_id: 项目ID
        :param chapter_index: 章节索引
        :return: 章节摘要对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            statement = select(ChapterSummary).where(
                ChapterSummary.project_id == project_id,
                ChapterSummary.chapter_index == chapter_index
            )
            summary = db.exec(statement).first()
            if summary:
                db.expunge(summary)
                logger.debug(f"获取章节摘要: {project_id} chapter {chapter_index}")
            else:
                logger.warning(f"章节摘要不存在: {project_id} chapter {chapter_index}")
            return summary

    @classmethod
    def list(cls, project_id: str, limit: Optional[int] = None, offset: int = 0) -> list[
        ChapterSummary]:
        """
        根据会话 ID 获取章节摘要列表。

        :param project_id: 会话 ID
        :param limit: 返回数量限制（None 表示无限制）
        :param offset: 跳过的记录数
        :return: 章节摘要列表
        """
        with DatabaseSession() as db:
            statement = select(ChapterSummary).where(ChapterSummary.project_id == project_id).offset(offset)
            if limit is not None:
                statement = statement.limit(limit)

            summaries = db.exec(statement).all()
            for summary in summaries:
                db.expunge(summary)
            logger.debug(f"获取会话 {project_id} 的章节摘要: {len(summaries)} 条")
            return list(summaries)

    @classmethod
    def update(cls, project_id: str, chapter_index: int, **kwargs) -> Optional[ChapterSummary]:
        """
        更新章节摘要。

        :param project_id: 项目ID
        :param chapter_index: 章节索引
        :param kwargs: 要更新的字段
        :return: 更新后的章节摘要对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            statement = select(ChapterSummary).where(
                ChapterSummary.project_id == project_id,
                ChapterSummary.chapter_index == chapter_index
            )
            summary = db.exec(statement).first()
            if not summary:
                logger.warning(f"章节摘要不存在，无法更新: {project_id} chapter {chapter_index}")
                return None

            # 更新字段
            for field, value in kwargs.items():
                if hasattr(summary, field):
                    setattr(summary, field, value)

            db.add(summary)
            db.flush()
            db.refresh(summary)
            db.expunge(summary)
            logger.info(f"更新章节摘要: {project_id} chapter {chapter_index}")
            return summary

    @classmethod
    def remove(cls, project_id: str, chapter_index: int) -> bool:
        """
        删除章节摘要。

        :param project_id: 项目ID
        :param chapter_index: 章节索引
        :return: 是否删除成功
        """
        with DatabaseSession() as db:
            statement = select(ChapterSummary).where(
                ChapterSummary.project_id == project_id,
                ChapterSummary.chapter_index == chapter_index
            )
            summary = db.exec(statement).first()
            if not summary:
                logger.warning(f"章节摘要不存在，无法删除: {project_id} chapter {chapter_index}")
                return False

            db.delete(summary)
            logger.info(f"删除章节摘要: {project_id} chapter {chapter_index}")
            return True
    
    @classmethod
    def clear(cls, project_id: str) -> int:
        """
        删除指定项目的所有章节摘要。

        :param project_id: 项目ID
        :return: 删除的记录数
        """
        with DatabaseSession() as db:
            statement = select(ChapterSummary).where(ChapterSummary.project_id == project_id)
            summaries = db.exec(statement).all()
            count = len(summaries)
            for summary in summaries:
                db.delete(summary)
            logger.info(f"删除项目 {project_id} 的所有章节摘要: {count} 条")
            return count
