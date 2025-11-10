"""限流配置设置。"""
from pydantic import BaseModel, Field


class RateLimitSettings(BaseModel):
    """限流配置。
    
    用于控制 API 请求的频率限制。
    """
    enabled: bool = Field(default=True, description="是否启用限流")
    global_per_minute: int = Field(default=1000000, ge=1, description="全局每分钟请求限制")
    login_per_minute: int = Field(default=100000, ge=1, description="登录接口每分钟请求限制")
    burst: int = Field(default=100000, ge=1, description="突发请求容量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "global_per_minute": 60,
                "login_per_minute": 10,
                "burst": 100
            }
        }
