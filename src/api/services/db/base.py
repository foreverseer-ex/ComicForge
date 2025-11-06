"""
数据库模块。

使用 SQLModel + SQLite 来管理应用数据。
"""

from loguru import logger
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import inspect, text

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


def _migrate_job_table() -> None:
    """
    迁移 job 表，添加新列（如果不存在）。
    
    这是一个简单的迁移函数，用于向后兼容。
    """
    inspector = inspect(engine)
    
    # 检查 job 表是否存在
    if "job" not in inspector.get_table_names():
        logger.debug("job 表不存在，将在 init_db 中创建")
        return
    
    columns = [col["name"] for col in inspector.get_columns("job")]
    has_changes = False
    
    # 添加 draw_args 列（如果不存在）
    if "draw_args" not in columns:
        logger.info("正在为 job 表添加 draw_args 列...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE job ADD COLUMN draw_args TEXT"))
            conn.commit()
        logger.success("已为 job 表添加 draw_args 列")
        has_changes = True
    
    # 添加 name 列（如果不存在）
    if "name" not in columns:
        logger.info("正在为 job 表添加 name 列...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE job ADD COLUMN name TEXT"))
            conn.commit()
        logger.success("已为 job 表添加 name 列")
        has_changes = True
    
    # 添加 desc 列（如果不存在）
    if "desc" not in columns:
        logger.info("正在为 job 表添加 desc 列...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE job ADD COLUMN desc TEXT"))
            conn.commit()
        logger.success("已为 job 表添加 desc 列")
        has_changes = True
    
    # 添加 completed_at 列（如果不存在）
    if "completed_at" not in columns:
        logger.info("正在为 job 表添加 completed_at 列...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE job ADD COLUMN completed_at TIMESTAMP"))
            conn.commit()
        logger.success("已为 job 表添加 completed_at 列")
        has_changes = True
    
    if not has_changes:
        logger.debug("job 表已包含所有必要列，无需迁移")


def init_db() -> None:
    """
    初始化数据库，创建所有表。
    
    应在应用启动时调用一次。
    """
    # 导入所有模型以确保它们被注册到 SQLModel.metadata

    # 创建所有表
    SQLModel.metadata.create_all(engine)
    logger.success(f"数据库已初始化: {database_path}")
    
    # 执行迁移
    try:
        _migrate_job_table()
    except Exception as e:
        logger.warning(f"数据库迁移失败（可能表已存在）: {e}")


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
