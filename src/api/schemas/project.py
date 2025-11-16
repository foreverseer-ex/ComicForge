"""
项目相关的数据模型。

每次小说转漫画任务都是一个项目，包含项目配置、进度状态等信息。
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


def generate_project_id() -> str:
    """
    生成项目ID（不带连字符的UUID）。
    
    返回32位十六进制字符串，只包含数字和字母，保持UUID的随机性。
    例如：f07916f0f4974754a6c404273e557519
    """
    return uuid.uuid4().hex


class Project(SQLModel, table=True):
    """项目主体。"""
    project_id: Optional[str] = Field(description="项目唯一标识", primary_key=True, default_factory=generate_project_id)
    title: str = Field(description="项目标题", index=True)
    novel_path: Optional[str] = Field(default=None, description="小说文件路径")
    project_path: str = Field(description="项目存储路径")

    # 小说元数据
    total_lines: int = Field(default=0, ge=0, description="小说总行数（段落数）")
    total_chapters: int = Field(default=0, ge=0, description="小说总章节数")
    current_line: int = Field(default=0, description="当前处理段落")
    current_chapter: int = Field(default=0, description="当前处理章节", index=True)

    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
