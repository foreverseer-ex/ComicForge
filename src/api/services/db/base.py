"""
数据库模块。

使用 SQLModel + SQLite 来管理应用数据。
"""

from typing import Optional
from loguru import logger
from sqlmodel import SQLModel, create_engine, Session

# noqa 标记：这些导入是必需的，用于注册表到 SQLModel.metadata
from api.schemas import *
from api.utils.path import database_path

# 创建数据库引擎
# check_same_thread=False 允许多线程访问（SQLite 默认只允许创建线程访问）
# echo=False 不打印 SQL 语句（生产环境建议设置为 False）
DATABASE_URL = f"sqlite:///{database_path}"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


def init_db() -> None:
    """
    初始化数据库，创建所有表。
    
    应在应用启动时调用一次。
    """
    # 导入所有模型以确保它们被注册到 SQLModel.metadata

    # 创建所有表
    SQLModel.metadata.create_all(engine)


def drop_all_tables() -> None:
    """
    删除数据库中的所有表。
    
    ⚠️ 危险操作：将删除所有数据！
    """
    # 删除所有表
    SQLModel.metadata.drop_all(engine)
    logger.warning(f"已删除数据库所有表: {database_path}")


# 便捷的上下文管理器
class DatabaseSession:
    """
    数据库会话上下文管理器。
    
    使用示例：
    ```python
    from services.db import DatabaseSession
    
    with DatabaseSession() as db:
        items = db.exec(select(Item)).all()
        # 自动提交和关闭
    ```
    """

    def __init__(self):
        """初始化数据库会话上下文管理器"""
        self.session: Session | None = None

    def __enter__(self) -> Session:
        """进入上下文，创建会话"""
        self.session = Session(engine)
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，关闭会话"""
        if self.session is None:
            return

        if exc_type is not None:
            # 发生异常时回滚
            self.session.rollback()
        else:
            # 正常退出时提交
            self.session.commit()

        self.session.close()


def normalize_project_id(project_id: Optional[str]) -> Optional[str]:
    """
    规范化 project_id，将字符串 "null" 转换为 None。
    
    当 LLM 调用工具时，JSON 中的 None 会被序列化为 "null" 字符串，
    导致数据库查询失败。此函数用于统一处理这种情况。
    
    :param project_id: 原始 project_id（可能是 None、"null" 或正常字符串）
    :return: 规范化后的 project_id（None 或正常字符串）
    """
    if project_id == "null":
        return None
    return project_id
