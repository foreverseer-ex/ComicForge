"""
绘图迭代数据库服务。

提供 DrawIteration 的增删改查操作。
"""
from typing import Optional
from loguru import logger
from sqlmodel import select, func

from .base import DatabaseSession, normalize_project_id
from api.schemas.memory import DrawIteration


class DrawIterationService:
    """
    绘图迭代数据库服务（单例模式）。
    
    使用类方法提供统一的 CRUD 接口。
    """
    
    @classmethod
    def create(cls, iteration: DrawIteration) -> DrawIteration:
        """
        创建绘图迭代记录。
        
        :param iteration: 绘图迭代对象
        :return: 创建后的对象
        """
        with DatabaseSession() as db:
            db.add(iteration)
            db.flush()
            db.refresh(iteration)
            db.expunge(iteration)
            logger.info(f"创建绘图迭代: project={iteration.project_id}, index={iteration.index}")
            return iteration
    
    @classmethod
    def get(cls, project_id: str, index: int) -> Optional[DrawIteration]:
        """
        根据项目ID和索引获取绘图迭代记录。
        
        :param project_id: 项目ID
        :param index: 迭代索引
        :return: 绘图迭代对象，如果不存在则返回 None
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            statement = select(DrawIteration).where(
                DrawIteration.project_id == project_id,
                DrawIteration.index == index
            )
            iteration = db.exec(statement).first()
            if iteration:
                db.expunge(iteration)
            return iteration
    
    @classmethod
    def get_by_id(cls, iteration_id: int) -> Optional[DrawIteration]:
        """
        根据 ID 获取绘图迭代记录。
        
        :param iteration_id: 迭代ID
        :return: 绘图迭代对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            iteration = db.get(DrawIteration, iteration_id)
            if iteration:
                db.expunge(iteration)
            return iteration
    
    @classmethod
    def get_max_index_before(cls, project_id: str, index: int) -> Optional[DrawIteration]:
        """
        获取指定索引之前（小于）的最大索引记录。
        
        :param project_id: 项目ID
        :param index: 当前索引
        :return: 绘图迭代对象，如果不存在则返回 None
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            # 查询 index < 指定 index 且 index 最大的记录
            statement = select(DrawIteration).where(
                DrawIteration.project_id == project_id,
                DrawIteration.index < index
            ).order_by(DrawIteration.index.desc()).limit(1)
            iteration = db.exec(statement).first()
            if iteration:
                db.expunge(iteration)
            return iteration
    
    @classmethod
    def update(cls, project_id: str, index: int, status: Optional[str] = None, summary: Optional[str] = None, draw_args: Optional[dict] = None) -> Optional[DrawIteration]:
        """
        更新绘图迭代记录。
        
        :param project_id: 项目ID
        :param index: 迭代索引
        :param status: 任务状态（可选）
        :param summary: 迭代摘要（可选）
        :param draw_args: 绘图参数（可选）
        :return: 更新后的对象，如果不存在则返回 None
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            statement = select(DrawIteration).where(
                DrawIteration.project_id == project_id,
                DrawIteration.index == index
            )
            iteration = db.exec(statement).first()
            if not iteration:
                return None
            
            if status is not None:
                iteration.status = status
            if summary is not None:
                iteration.summary = summary
            if draw_args is not None:
                iteration.draw_args = draw_args
            
            db.flush()
            db.refresh(iteration)
            db.expunge(iteration)
            logger.info(f"更新绘图迭代: project={project_id}, index={index}, status={status}")
            return iteration
    
    @classmethod
    def delete_range(cls, project_id: str, start_index: int, end_index: int) -> int:
        """
        删除指定范围内的所有绘图迭代记录。
        
        :param project_id: 项目ID
        :param start_index: 起始索引（包含）
        :param end_index: 结束索引（包含）
        :return: 删除的记录数量
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            statement = select(DrawIteration).where(
                DrawIteration.project_id == project_id,
                DrawIteration.index >= start_index,
                DrawIteration.index <= end_index
            )
            iterations = list(db.exec(statement).all())
            if not iterations:
                return 0
            
            deleted_count = len(iterations)
            for iteration in iterations:
                db.delete(iteration)
            db.flush()
            logger.info(f"删除绘图迭代范围: project={project_id}, start_index={start_index}, end_index={end_index}, 删除数量={deleted_count}")
            return deleted_count
    
    @classmethod
    def get_max_index_before_or_equal(cls, project_id: str, index: int) -> Optional[DrawIteration]:
        """
        获取指定索引之前或等于（<=）的最大索引记录。
        
        :param project_id: 项目ID
        :param index: 当前索引
        :return: 绘图迭代对象，如果不存在则返回 None
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            # 查询 index <= 指定 index 且 index 最大的记录
            statement = select(DrawIteration).where(
                DrawIteration.project_id == project_id,
                DrawIteration.index <= index
            ).order_by(DrawIteration.index.desc()).limit(1)
            iteration = db.exec(statement).first()
            if iteration:
                db.expunge(iteration)
            return iteration
    
    @classmethod
    def cancel_pending_after_index(cls, project_id: str, start_index: int) -> int:
        """
        将指定索引之后的所有 pending 状态的 DrawIteration 更新为 cancelled。
        
        :param project_id: 项目ID
        :param start_index: 起始索引（不包含，即从 start_index + 1 开始）
        :return: 更新的记录数量
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            statement = select(DrawIteration).where(
                DrawIteration.project_id == project_id,
                DrawIteration.index > start_index,
                DrawIteration.status == "pending"
            )
            iterations = list(db.exec(statement).all())
            if not iterations:
                return 0
            
            updated_count = len(iterations)
            for iteration in iterations:
                iteration.status = "cancelled"
            db.flush()
            logger.info(f"取消 pending 状态的 DrawIteration: project={project_id}, start_index={start_index}, 更新数量={updated_count}")
            return updated_count
    
    @classmethod
    def delete_all(cls, project_id: str) -> int:
        """
        删除指定项目的所有 DrawIteration 记录。
        
        :param project_id: 项目ID
        :return: 删除的记录数量
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            statement = select(DrawIteration).where(
                DrawIteration.project_id == project_id
            )
            iterations = list(db.exec(statement).all())
            if not iterations:
                return 0
            
            deleted_count = len(iterations)
            for iteration in iterations:
                db.delete(iteration)
            db.flush()
            logger.info(f"删除所有 DrawIteration: project={project_id}, 删除数量={deleted_count}")
            return deleted_count
    
    @classmethod
    def delete(cls, project_id: str, index: int) -> bool:
        """
        删除绘图迭代记录（删除所有匹配的记录，防止重复）。
        
        :param project_id: 项目ID
        :param index: 迭代索引
        :return: 是否成功删除（至少删除了一条记录）
        """
        project_id = normalize_project_id(project_id)
        with DatabaseSession() as db:
            statement = select(DrawIteration).where(
                DrawIteration.project_id == project_id,
                DrawIteration.index == index
            )
            iterations = list(db.exec(statement).all())
            if not iterations:
                return False
            
            # 删除所有匹配的记录（防止重复）
            deleted_count = len(iterations)
            for iteration in iterations:
                db.delete(iteration)
            db.flush()
            logger.info(f"删除绘图迭代: project={project_id}, index={index}, 删除数量={deleted_count}")
            return True

