"""
FastAPI 应用入口文件。

启动 FastAPI 服务，注册所有路由，初始化数据库。
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import logging

from api.routers import (
    project,
    actor,
    memory,
    file,
    draw,
    llm,
    context,
    chat,
    history,
    settings,
    help,
    model_meta,
    auth,
)
from api.services.db.base import init_db
from api.services.admin_init import init_admin_user
from api.settings import app_settings

# 配置 uvicorn.access logger：过滤掉 /health 端点的访问日志
class HealthCheckFilter(logging.Filter):
    """过滤掉 /health 端点的访问日志"""
    def filter(self, record):
        # 检查日志消息中是否包含 /health
        message = record.getMessage()
        if "/health" in message:
            return False
        return True

# 获取 uvicorn.access logger 并添加过滤器
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addFilter(HealthCheckFilter())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期事件处理器"""
    # 启动时执行
    # 初始化数据库
    init_db()
    
    # 初始化管理员账户
    init_admin_user()
    
    yield
    
    # 关闭时执行


# 创建 FastAPI 应用实例
app = FastAPI(
    title="ComicForge API",
    description="AI 驱动的漫画创作与可视化工具 API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置 CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7863", "http://127.0.0.1:7863"],  # 前端端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有路由
app.include_router(project.router)
app.include_router(actor.router)
app.include_router(memory.router)
app.include_router(file.router)
app.include_router(draw.router)
app.include_router(llm.router)
app.include_router(context.router)
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(settings.router)
app.include_router(help.router)
app.include_router(model_meta.router)
app.include_router(auth.router)



@app.get("/", tags=["根路径"])
async def root():
    """根路径，返回 API 信息"""
    return {
        "name": "ComicForge API",
        "version": "0.1.0",
        "description": "AI 驱动的漫画创作与可视化工具 API",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}

