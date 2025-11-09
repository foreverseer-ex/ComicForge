"""数据库化的模型元数据定义（SQLModel）。"""
from pathlib import Path
from typing import Literal, TYPE_CHECKING, Any
import httpx
from pydantic import BaseModel, computed_field
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from api.utils.civitai import AIR

if TYPE_CHECKING:
    from .draw import DrawArgs


class Example(BaseModel):
    """单个示例图片引用及其对应生成参数（仅用于序列化，DB 中以 dict 列表存储）。"""
    url: str | None = None
    # 兼容：避免 forward ref 与 | 运算在 Py3.13 报错，这里保持为可选 dict
    args: dict[str, Any] | None = None

    @property
    def filename(self) -> Path | None:
        if self.url is None:
            return None
        return Path(httpx.URL(self.url).path.split('/')[-1])


class ModelMeta(SQLModel, table=True):
    """
    模型元数据（数据库表）。
    
    - 使用 version_id 作为主键（Civitai 的版本 ID）
    - list/dict 字段使用 JSON 列存储
    - 示例图片文件仍存本地；DB 仅存示例的元信息（url/args）
    """
    version_id: int = Field(primary_key=True)
    filename: str
    name: str
    version: str
    desc: str | None = None
    model_id: int
    type: str
    ecosystem: str
    base_model: str | None = None
    sha256: str
    trained_words: list[str] = Field(default_factory=list, sa_column=Column(SQLITE_JSON))
    url: str | None = None
    web_page_url: str | None = None
    examples: list[dict] = Field(default_factory=list, sa_column=Column(SQLITE_JSON))
    preference: str = 'neutral'

    @computed_field
    @property
    def version_name(self) -> str:
        return f"{self.name}-{self.version}"

    @computed_field
    @property
    def air(self) -> str:
        air = AIR(
            ecosystem=self.ecosystem,
            type=self.type,
            model_id=self.model_id,
            version_id=self.version_id,
        )
        return str(air)
