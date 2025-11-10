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
    
    根据配置文件中的管理员设置，创建或更新管理员账户：
    1. 如果配置中的用户名不存在，则创建新管理员账户
    2. 如果配置中的用户名已存在：
       - 如果是管理员角色，则更新密码
       - 如果不是管理员角色，则删除旧账户并创建新管理员账户
    3. 删除所有其他管理员账户（只保留配置中指定的管理员）
    """
    admin_config = app_settings.admin
    logger.info(f"初始化管理员账户: {admin_config.username}")
    
    try:
        with DatabaseSession() as db:
            # 查找配置中的用户名
            target_user = db.exec(
                select(User).where(User.username == admin_config.username)
            ).first()
            
            # 查找所有管理员用户
            all_admins = db.exec(
                select(User).where(User.role == "admin")
            ).all()
            
            # 删除其他管理员账户（不是配置中指定的）
            for admin in all_admins:
                if admin.username != admin_config.username:
                    logger.info(f"删除旧管理员账户: {admin.username}")
                    db.delete(admin)
            
            # 处理目标管理员账户
            if target_user is None:
                # 不存在，创建新管理员
                new_admin = User(
                    username=admin_config.username,
                    password_hash=hash_password(admin_config.password),
                    role="admin",
                    is_active=True,
                )
                db.add(new_admin)
                logger.success(f"管理员账户创建成功: {admin_config.username}")
                
            elif target_user.role != "admin":
                # 存在但不是管理员，删除并重新创建
                logger.warning(f"用户 {admin_config.username} 不是管理员，删除并重新创建")
                db.delete(target_user)
                db.flush()
                
                new_admin = User(
                    username=admin_config.username,
                    password_hash=hash_password(admin_config.password),
                    role="admin",
                    is_active=True,
                )
                db.add(new_admin)
                logger.success(f"管理员账户重新创建成功: {admin_config.username}")
                
            else:
                # 已存在且是管理员，更新密码
                target_user.password_hash = hash_password(admin_config.password)
                target_user.is_active = True  # 确保账户处于启用状态
                logger.success(f"管理员账户密码已更新: {admin_config.username}")
            
            # 提交由 DatabaseSession 上下文自动完成
            
    except Exception as e:
        logger.exception(f"初始化管理员账户失败: {e}")
        raise
