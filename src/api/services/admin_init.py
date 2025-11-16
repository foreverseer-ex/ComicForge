"""管理员账户初始化服务。

在应用启动时自动创建或更新管理员账户。
"""
from loguru import logger
from sqlmodel import select

from api.services.db import DatabaseSession
from api.schemas.user import User
from api.security import hash_password
from api.settings import app_settings


def init_admin_user():
    """初始化管理员用户。
    
    根据配置文件中的管理员设置，创建管理员账户：
    1. 先删除所有之前的管理员账户（包括配置中指定的那个，如果存在）
    2. 然后根据 config.json 里的内容建立新的管理员账户
    """
    admin_config = app_settings.admin
    
    try:
        with DatabaseSession() as db:
            # 查找所有管理员用户
            all_admins = db.exec(
                select(User).where(User.role == "admin")
            ).all()
            
            # 删除所有之前的管理员账户
            for admin in all_admins:
                logger.debug(f"删除旧的管理员账户: {admin.username}")
                db.delete(admin)
            
            # 确保删除操作完成
            db.flush()
            
            # 根据 config.json 创建新的管理员账户
            new_admin = User(
                username=admin_config.username,
                password_hash=hash_password(admin_config.password),
                role="admin",
                is_active=True,
            )
            db.add(new_admin)
            logger.debug(f"创建新的管理员账户: {admin_config.username}")
            
            # 提交由 DatabaseSession 上下文自动完成
            
    except Exception as e:
        logger.exception(f"初始化管理员账户失败: {e}")
        raise
