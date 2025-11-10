"""管理员配置设置。"""
from typing import Optional
from pydantic import BaseModel, Field


class AdminSettings(BaseModel):
    """管理员账户配置。
    
    管理员账户在应用启动时自动创建或更新。
    """
    username: str = Field(default="admin", description="管理员用户名")
    password: str = Field(default="admin123", description="管理员密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "change_this_password"
            }
        }
