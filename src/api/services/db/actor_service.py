"""
Actor（角色/要素）数据库服务。

提供 Actor 的增删改查操作。
Actor 可以是角色、地点、组织等小说要素。
"""
from typing import Optional
from loguru import logger
from sqlmodel import select

from .base import DatabaseSession
from api.schemas.actor import Actor, ActorExample


class ActorService:
    """
    Actor 数据库服务（单例模式）。
    
    使用类方法提供统一的 CRUD 接口。
    """
    
    @classmethod
    def create(cls, actor: Actor) -> Actor:
        """
        创建 Actor。
        
        :param actor: Actor 对象
        :return: 创建后的 Actor 对象
        """
        with DatabaseSession() as db:
            db.add(actor)
            db.flush()
            db.refresh(actor)
            db.expunge(actor)
            logger.info(f"创建 Actor: {actor.name}")
            return actor
    
    @classmethod
    def get(cls, actor_id: str) -> Optional[Actor]:
        """
        根据 actor_id 获取 Actor。
        
        :param actor_id: Actor ID
        :return: Actor 对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            actor = db.get(Actor, actor_id)
            if actor:
                db.expunge(actor)
                logger.debug(f"获取 Actor: {actor_id}")
            else:
                logger.warning(f"Actor 不存在: {actor_id}")
            return actor
    
    @classmethod
    def list_by_session(cls, project_id: str, limit: Optional[int] = None, offset: int = 0) -> list[Actor]:
        """
        根据项目ID获取 Actor 列表。
        
        :param project_id: 项目ID
        :param limit: 返回数量限制（None 表示无限制）
        :param offset: 跳过的记录数
        :return: Actor 列表
        """
        with DatabaseSession() as db:
            statement = select(Actor).where(Actor.project_id == project_id).offset(offset)
            if limit is not None:
                statement = statement.limit(limit)
            
            actors = db.exec(statement).all()
            for actor in actors:
                db.expunge(actor)
            logger.debug(f"获取 Actor 列表: {len(actors)} 条")
            return list(actors)
    
    @classmethod
    def update(cls, actor_id: str, **kwargs) -> Optional[Actor]:
        """
        更新 Actor。
        
        :param actor_id: Actor ID
        :param kwargs: 要更新的字段
        :return: 更新后的 Actor 对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            actor = db.get(Actor, actor_id)
            if not actor:
                logger.warning(f"Actor 不存在，无法更新: {actor_id}")
                return None
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(actor, key):
                    setattr(actor, key, value)
            
            db.add(actor)
            db.flush()
            db.refresh(actor)
            db.expunge(actor)
            logger.info(f"更新 Actor: {actor_id}")
            return actor
    
    @classmethod
    def delete(cls, actor_id: str) -> bool:
        """
        删除 Actor。
        
        :param actor_id: Actor ID
        :return: 是否删除成功
        """
        with DatabaseSession() as db:
            actor = db.get(Actor, actor_id)
            if not actor:
                logger.warning(f"Actor 不存在，无法删除: {actor_id}")
                return False
            
            db.delete(actor)
            logger.info(f"删除 Actor: {actor_id}")
            return True
    
    @classmethod
    def add_example(cls, actor_id: str, example: ActorExample) -> Optional[Actor]:
        """
        为 Actor 添加示例图。
        
        :param actor_id: Actor ID
        :param example: ActorExample 对象
        :return: 更新后的 Actor 对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            actor = db.get(Actor, actor_id)
            if not actor:
                logger.warning(f"Actor 不存在，无法添加示例: {actor_id}")
                return None
            
            # 将 ActorExample 转换为字典并添加到 examples 列表
            actor.examples.append(example.model_dump())
            db.add(actor)
            db.flush()
            db.refresh(actor)
            db.expunge(actor)
            logger.info(f"为 Actor 添加示例: {actor_id}, title={example.title}")
            return actor
    
    @classmethod
    def remove_example(cls, actor_id: str, example_index: int) -> Optional[Actor]:
        """
        删除 Actor 的指定示例图。
        
        :param actor_id: Actor ID
        :param example_index: 示例图索引
        :return: 更新后的 Actor 对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            actor = db.get(Actor, actor_id)
            if not actor:
                logger.warning(f"Actor 不存在，无法删除示例: {actor_id}")
                return None
            
            if not (0 <= example_index < len(actor.examples)):
                logger.warning(f"示例图索引越界: {actor_id}, index={example_index}, 总数={len(actor.examples)}")
                return None
            
            # 记录删除前的状态（用于调试）
            logger.debug(f"删除前 examples 列表: {[ex.get('title', '未命名') for ex in actor.examples]}")
            logger.debug(f"要删除的索引: {example_index}, 对应的标题: {actor.examples[example_index].get('title', '未命名')}")
            
            # 记录要删除的示例信息（用于日志）
            removed_example = actor.examples[example_index]
            
            # 重新构建列表，排除指定索引的元素
            # 这样可以确保 MutableList 正确检测到变化
            new_examples = [
                actor.examples[i] 
                for i in range(len(actor.examples)) 
                if i != example_index
            ]
            
            # 使用切片赋值来替换整个列表，确保 MutableList 检测到变化
            actor.examples[:] = new_examples
            
            # 标记对象为已修改（确保 SQLAlchemy 检测到变化）
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(actor, "examples")
            
            db.add(actor)
            db.flush()
            db.refresh(actor)
            db.expunge(actor)
            
            # 记录删除后的状态（用于调试）
            logger.debug(f"删除后 examples 列表: {[ex.get('title', '未命名') for ex in actor.examples]}")
            logger.info(f"删除 Actor 示例: {actor_id}, index={example_index}, title={removed_example.get('title')}, 剩余数量={len(actor.examples)}")
            return actor
    
    @classmethod
    def swap_examples(cls, actor_id: str, index1: int, index2: int) -> Optional[Actor]:
        """
        交换两个示例图的位置。
        
        :param actor_id: Actor ID
        :param index1: 第一个示例图的索引
        :param index2: 第二个示例图的索引
        :return: 更新后的 Actor 对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            actor = db.get(Actor, actor_id)
            if not actor:
                logger.warning(f"Actor 不存在，无法交换示例: {actor_id}")
                return None
            
            if index1 == index2:
                # 如果两个索引相同，不需要交换
                logger.debug(f"示例图索引相同，无需交换: {actor_id}, index={index1}")
                return actor
            
            if not (0 <= index1 < len(actor.examples) and 0 <= index2 < len(actor.examples)):
                logger.warning(f"示例图索引越界: {actor_id}, index1={index1}, index2={index2}")
                return None
            
            # 交换两个示例图
            actor.examples[index1], actor.examples[index2] = actor.examples[index2], actor.examples[index1]
            db.add(actor)
            db.flush()
            db.refresh(actor)
            db.expunge(actor)
            logger.info(f"交换 Actor 示例: {actor_id}, index1={index1}, index2={index2}")
            return actor
    
    @classmethod
    def update_example(cls, actor_id: str, example_index: int, example: ActorExample) -> Optional[Actor]:
        """
        更新 Actor 的指定示例图。
        
        :param actor_id: Actor ID
        :param example_index: 示例图索引
        :param example: 新的 ActorExample 对象
        :return: 更新后的 Actor 对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            actor = db.get(Actor, actor_id)
            if not actor:
                logger.warning(f"Actor 不存在，无法更新示例: {actor_id}")
                return None
            
            if 0 <= example_index < len(actor.examples):
                actor.examples[example_index] = example.model_dump()
                db.add(actor)
                db.flush()
                db.refresh(actor)
                db.expunge(actor)
                logger.info(f"更新 Actor 示例: {actor_id}, index={example_index}, title={example.title}")
                return actor
            else:
                logger.warning(f"示例图索引越界: {actor_id}, index={example_index}")
                return None
    
    @classmethod
    def clear_examples(cls, actor_id: str) -> Optional[Actor]:
        """
        清空 Actor 的所有示例图。
        
        :param actor_id: Actor ID
        :return: 更新后的 Actor 对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            actor = db.get(Actor, actor_id)
            if not actor:
                logger.warning(f"Actor 不存在，无法清空示例: {actor_id}")
                return None
            
            # 清空 examples 列表
            actor.examples.clear()
            
            # 标记对象为已修改（确保 SQLAlchemy 检测到变化）
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(actor, "examples")
            
            db.add(actor)
            db.flush()
            db.refresh(actor)
            db.expunge(actor)
            logger.info(f"清空 Actor 所有示例: {actor_id}")
            return actor
    
    @classmethod
    def batch_remove_examples(cls, actor_id: str, example_indices: list[int]) -> Optional[Actor]:
        """
        批量删除 Actor 的示例图。
        
        :param actor_id: Actor ID
        :param example_indices: 要删除的示例图索引列表（按降序排列，避免删除时索引变化）
        :return: 更新后的 Actor 对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            actor = db.get(Actor, actor_id)
            if not actor:
                logger.warning(f"Actor 不存在，无法批量删除示例: {actor_id}")
                return None
            
            if not actor.examples:
                logger.debug(f"Actor 没有示例图，无需删除: {actor_id}")
                return actor
            
            # 验证索引有效性
            valid_indices = [idx for idx in example_indices if 0 <= idx < len(actor.examples)]
            if not valid_indices:
                logger.warning(f"没有有效的示例图索引: {actor_id}, indices={example_indices}")
                return actor
            
            # 去重并排序（降序，从后往前删除，避免索引变化）
            valid_indices = sorted(set(valid_indices), reverse=True)
            
            # 记录删除前的状态（用于调试）
            logger.debug(f"批量删除前 examples 列表: {[ex.get('title', '未命名') for ex in actor.examples]}")
            logger.debug(f"要删除的索引: {valid_indices}")
            
            # 从后往前删除，避免索引变化
            for idx in valid_indices:
                if 0 <= idx < len(actor.examples):
                    actor.examples.pop(idx)
            
            # 标记对象为已修改（确保 SQLAlchemy 检测到变化）
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(actor, "examples")
            
            db.add(actor)
            db.flush()
            db.refresh(actor)
            db.expunge(actor)
            
            # 记录删除后的状态（用于调试）
            logger.debug(f"批量删除后 examples 列表: {[ex.get('title', '未命名') for ex in actor.examples]}")
            logger.info(f"批量删除 Actor 示例: {actor_id}, 删除了 {len(valid_indices)} 个示例, 剩余数量={len(actor.examples)}")
            return actor

