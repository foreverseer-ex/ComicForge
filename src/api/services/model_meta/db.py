"""
数据库版的模型元数据服务。

- 使用 SQLModel 的 ModelMeta 表
- examples/trained_words 等使用 JSON 列
- 示例图片仍下载到本地文件夹；DB 只存元信息（url/args）
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from loguru import logger

from sqlmodel import select

from api.schemas.model_meta import ModelMeta, Example
from api.schemas.model_meta import ModelMeta as ModelMetaTable
from api.services.db.base import DatabaseSession  # 复用现有 DB Session 管理
from api.settings import app_settings
from api.utils.path import checkpoint_meta_home, lora_meta_home
from api.utils.download import download_file


class ModelMetaDbService:
    """数据库版 ModelMeta 服务。"""

    # ====== 基本查询 ======
    def get_by_id(self, version_id: int) -> Optional[ModelMeta]:
        with DatabaseSession() as db:
            meta = db.get(ModelMetaTable, version_id)
            if meta:
                db.expunge(meta)
            return meta

    def get_by_version_name(self, version_name: str) -> Optional[ModelMeta]:
        with DatabaseSession() as db:
            statement = select(ModelMetaTable).where(
                (ModelMetaTable.name + "-" + ModelMetaTable.version) == version_name
            )
            meta = db.exec(statement).first()
            if meta:
                db.expunge(meta)
            return meta

    def get_by_name(self, name: str) -> Optional[ModelMeta]:
        with DatabaseSession() as db:
            statement = select(ModelMetaTable).where(ModelMetaTable.name == name)
            meta = db.exec(statement).first()
            if meta:
                db.expunge(meta)
            return meta

    def get_by_filename(self, filename: str) -> Optional[ModelMeta]:
        stem = Path(filename).stem
        with DatabaseSession() as db:
            statement = select(ModelMetaTable)
            metas = db.exec(statement).all()
            for m in metas:
                if Path(m.filename).stem == stem:
                    db.expunge(m)
                    return m
            return None

    # 类型筛选
    def list_by_type(self, type_: str) -> List[ModelMeta]:
        with DatabaseSession() as db:
            statement = select(ModelMetaTable).where(ModelMetaTable.type == type_)
            metas = db.exec(statement).all()
            for m in metas:
                db.expunge(m)
            return list(metas)

    @property
    def sd_list(self) -> List[ModelMeta]:
        return self.list_by_type('checkpoint')

    @property
    def lora_list(self) -> List[ModelMeta]:
        return self.list_by_type('lora')

    @property
    def vae_list(self) -> List[ModelMeta]:
        return self.list_by_type('vae')

    # ====== 保存/删除 ======
    async def save(self, model_meta: ModelMeta, *, parallel_download: bool = False, download_examples: bool = True) -> Tuple[ModelMeta, int, int]:
        """
        下载示例图片到本地（可选），并将元数据写入数据库。
        返回 (保存后的 ModelMeta, 失败图片数, 总图片数)
        """
        # 确定存放目录
        home = checkpoint_meta_home if model_meta.type == 'checkpoint' else lora_meta_home
        base_path = home / Path(model_meta.filename).stem
        base_path.mkdir(parents=True, exist_ok=True)

        # 处理示例图片
        failed_image_count = 0
        total_image_count = 0
        localized_examples: List[Dict[str, Any]] = []

        examples = model_meta.examples or []
        # 规范化为 Example 实例以便访问 filename
        example_objs: List[Example] = []
        for ex in examples:
            if isinstance(ex, dict):
                example_objs.append(Example(**ex))
            elif isinstance(ex, Example):
                example_objs.append(ex)

        if download_examples and example_objs:
            total_image_count = len(example_objs)
            if parallel_download:
                import asyncio
                tasks = []
                for ex in example_objs:
                    if ex.filename is None:
                        failed_image_count += 1
                        continue
                    save_path = base_path / ex.filename
                    tasks.append(download_file(ex.url, save_path, app_settings.civitai.timeout))
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for ex, ok in zip(example_objs, results):
                    if ok is True:
                        localized_examples.append({"url": ex.url, "args": getattr(ex, 'args', {})})
                    else:
                        failed_image_count += 1
            else:
                for ex in example_objs:
                    if ex.filename is None:
                        failed_image_count += 1
                        continue
                    save_path = base_path / ex.filename
                    ok = await download_file(ex.url, save_path, app_settings.civitai.timeout)
                    if ok:
                        localized_examples.append({"url": ex.url, "args": getattr(ex, 'args', {})})
                    else:
                        failed_image_count += 1
        else:
            for ex in example_objs:
                localized_examples.append({"url": ex.url, "args": getattr(ex, 'args', {})})

        # upsert 到数据库
        with DatabaseSession() as db:
            existing = db.get(ModelMetaTable, model_meta.version_id)
            payload = ModelMetaTable(
                version_id=model_meta.version_id,
                filename=model_meta.filename,
                name=model_meta.name,
                version=model_meta.version,
                desc=model_meta.desc,
                model_id=model_meta.model_id,
                type=model_meta.type,
                ecosystem=model_meta.ecosystem,
                base_model=model_meta.base_model,
                sha256=model_meta.sha256,
                trained_words=list(getattr(model_meta, 'trained_words', []) or []),
                url=model_meta.url,
                web_page_url=model_meta.web_page_url,
                examples=localized_examples,
                preference=getattr(model_meta, 'preference', 'neutral'),
            )
            if existing:
                # 更新
                for field in payload.model_fields.keys():
                    setattr(existing, field, getattr(payload, field))
                db.add(existing)
                db.flush()
                db.refresh(existing)
                db.expunge(existing)
                saved = existing
            else:
                db.add(payload)
                db.flush()
                db.refresh(payload)
                db.expunge(payload)
                saved = payload

        logger.success(f"已保存模型元数据到数据库: {saved.name} ({saved.type})")
        return saved, failed_image_count, total_image_count

    async def delete(self, version_id: int) -> bool:
        """删除模型元数据（不强制删除本地图片目录）。"""
        with DatabaseSession() as db:
            meta = db.get(ModelMetaTable, version_id)
            if not meta:
                return False
            db.delete(meta)
            return True

    def set_preference(self, version_id: int, preference: str) -> Optional[ModelMeta]:
        """更新模型偏好。"""
        with DatabaseSession() as db:
            meta = db.get(ModelMetaTable, version_id)
            if not meta:
                return None
            meta.preference = preference
            db.add(meta)
            db.flush()
            db.refresh(meta)
            db.expunge(meta)
            return meta

    def get_all(self) -> List[ModelMeta]:
        with DatabaseSession() as db:
            metas = db.exec(select(ModelMetaTable)).all()
            for m in metas:
                db.expunge(m)
            return list(metas)

    def update_fields(self, version_id: int, **fields) -> Optional[ModelMeta]:
        """更新任意字段后返回最新记录。"""
        with DatabaseSession() as db:
            meta = db.get(ModelMetaTable, version_id)
            if not meta:
                return None
            for k, v in fields.items():
                if hasattr(meta, k):
                    setattr(meta, k, v)
            db.add(meta)
            db.flush()
            db.refresh(meta)
            db.expunge(meta)
            return meta


model_meta_db_service = ModelMetaDbService()
