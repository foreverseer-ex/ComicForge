"""
帮助管理的路由。

提供应用帮助文档的读取功能。
支持中文和英文两种语言。
"""
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from loguru import logger

router = APIRouter(
    prefix="/help",
    tags=["帮助文档"],
    responses={404: {"description": "帮助文档不存在"}},
)


def _load_readme(filename: str) -> str:
    """
    加载 README 文件内容。
    
    Args:
        filename: README 文件名（如 "README.md" 或 "README.en.md"）
    
    Returns:
        README 文件内容（Markdown 格式）
    """
    try:
        # 从项目根目录查找 README 文件
        # 从 src/api/routers/help.py 向上查找项目根目录（包含 pyproject.toml 或 package.json）
        current = Path(__file__).parent.parent.parent  # src/
        # 继续向上查找，直到找到项目根目录
        while current.parent != current:
            if (current / "pyproject.toml").exists() or (current / "package.json").exists():
                break
            current = current.parent
        project_root = current
        readme_path = project_root / filename
        
        if not readme_path.exists():
            logger.warning(f"帮助文档不存在: {readme_path}")
            raise FileNotFoundError(f"帮助文档文件不存在: {filename}")
        
        content = readme_path.read_text(encoding="utf-8")
        logger.info(f"已加载帮助文档: {readme_path}")
        return content
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"加载帮助文档 '{filename}' 失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载帮助文档失败: {str(e)}")


@router.get("/", summary="获取帮助文档", response_class=PlainTextResponse)
async def get_help_document(
    lang: Literal["zh", "en"] = Query("zh", description="语言选择：zh (中文) 或 en (英文)")
) -> str:
    """
    根据语言获取应用的帮助文档（Markdown 格式）。
    
    Args:
        lang: 语言选择，默认为中文。
    
    Returns:
        对应语言的帮助文档内容。
    """
    if lang == "en":
        filename = "README.en.md"
    else:
        filename = "README.md"
    
    return _load_readme(filename)

