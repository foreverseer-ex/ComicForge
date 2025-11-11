"""
数据库版的模型元数据服务。

- 使用 SQLModel 的 ModelMetaTable 表
- examples/trained_words 等使用 JSON 列
- 示例图片仍下载到本地文件夹；DB 只存元信息（url/args）
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

from loguru import logger

from sqlmodel import select, func

from api.schemas.model_meta import ModelMeta, Example, ModelMetaTable
from api.services.db.base import DatabaseSession  # 复用现有 DB Session 管理
from api.settings import app_settings
from api.utils.path import checkpoint_meta_home, lora_meta_home
from api.utils.download import download_file


class ModelMetaDbService:
    """数据库版 ModelMeta 服务。"""

    # ====== 基本查询 ======
    def get_by_id(self, version_id: int) -> Optional[ModelMeta]:
        """通过 version_id 获取模型元数据。"""
        with DatabaseSession() as db:
            meta_table = db.get(ModelMetaTable, version_id)
            if meta_table:
                db.expunge(meta_table)
                return ModelMeta.from_table(meta_table)
            return None

    def get_by_version_name(self, version_name: str) -> Optional[ModelMeta]:
        """通过 version_name (name-version) 获取模型元数据。"""
        with DatabaseSession() as db:
            # 由于 SQLite 可能不支持 CONCAT，使用 Python 端过滤
            statement = select(ModelMetaTable)
            metas = db.exec(statement).all()
            for meta_table in metas:
                if f"{meta_table.name}-{meta_table.version}" == version_name:
                    db.expunge(meta_table)
                    return ModelMeta.from_table(meta_table)
            return None

    def get_by_name(self, name: str) -> Optional[ModelMeta]:
        """通过 name 获取模型元数据（返回第一个匹配的）。"""
        with DatabaseSession() as db:
            statement = select(ModelMetaTable).where(ModelMetaTable.name == name)
            meta_table = db.exec(statement).first()
            if meta_table:
                db.expunge(meta_table)
                return ModelMeta.from_table(meta_table)
            return None

    def get_by_hash(self, file_hash: str) -> Optional[ModelMeta]:
        """通过文件哈希值获取模型元数据。"""
        with DatabaseSession() as db:
            statement = select(ModelMetaTable).where(ModelMetaTable.sha256 == file_hash)
            meta_table = db.exec(statement).first()
            if meta_table:
                db.expunge(meta_table)
                return ModelMeta.from_table(meta_table)
            return None

    def get_by_filename(self, filename: str) -> Optional[ModelMeta]:
        """通过文件名获取模型元数据。"""
        stem = Path(filename).stem
        with DatabaseSession() as db:
            statement = select(ModelMetaTable)
            metas = db.exec(statement).all()
            for m in metas:
                if Path(m.filename).stem == stem:
                    db.expunge(m)
                    return ModelMeta.from_table(m)
            return None

    # 类型筛选
    def list_by_type(self, type_: str) -> List[ModelMeta]:
        """根据类型获取模型列表。"""
        with DatabaseSession() as db:
            statement = select(ModelMetaTable).where(ModelMetaTable.type == type_)
            metas = db.exec(statement).all()
            result = []
            for m in metas:
                db.expunge(m)
                result.append(ModelMeta.from_table(m))
            return result

    @property
    def sd_list(self) -> List[ModelMeta]:
        """获取所有 Checkpoint 模型列表。"""
        return self.list_by_type('checkpoint')

    @property
    def lora_list(self) -> List[ModelMeta]:
        """获取所有 LoRA 模型列表。"""
        return self.list_by_type('lora')

    @property
    def vae_list(self) -> List[ModelMeta]:
        """获取所有 VAE 模型列表。"""
        return self.list_by_type('vae')
    
    def flush(self):
        """刷新缓存（数据库服务无需刷新，此方法为空实现以保持接口兼容）。"""
        # 数据库服务直接从数据库读取，无需刷新内存缓存
        pass

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

        # 将 Example 对象转换为字典以便存储到 JSON 列
        def example_to_dict(ex: Example) -> Dict[str, Any]:
            """将 Example 对象转换为字典。"""
            # Example 的 url 属性从 extra 中获取，所以我们需要确保 extra 中有 url
            ex_dict: Dict[str, Any] = {
                'title': ex.title,
                'desc': ex.desc,
                'filename': ex.filename or '',
            }
            
            # 处理 draw_args
            if ex.draw_args:
                ex_dict['draw_args'] = ex.draw_args.model_dump()
            else:
                ex_dict['draw_args'] = None
            
            # 处理 extra 字段
            if hasattr(ex, 'extra') and ex.extra:
                ex_dict['extra'] = dict(ex.extra)
            else:
                ex_dict['extra'] = {}
            
            # 如果 Example 有 url（通过属性访问），确保它在 extra 中
            # Example.url 属性从 extra.get('url') 读取
            url = getattr(ex, 'url', None) or ex_dict['extra'].get('url')
            if url:
                ex_dict['extra']['url'] = url
                # 同时保留顶层 url 字段（方便前端访问和序列化）
                ex_dict['url'] = url
            
            return ex_dict
        
        examples_dicts = []
        
        if download_examples and example_objs:
            total_image_count = len(example_objs)
            if parallel_download:
                import asyncio
                download_tasks = []
                download_examples_list = []
                
                # 先转换所有 examples 为字典（无论下载是否成功，都保存元数据）
                for ex in example_objs:
                    examples_dicts.append(example_to_dict(ex))
                    
                    # 准备下载任务
                    if ex.filename and ex.url:
                        save_path = base_path / ex.filename
                        download_tasks.append(download_file(ex.url, save_path, app_settings.civitai.timeout))
                        download_examples_list.append(ex)
                    else:
                        failed_image_count += 1
                
                # 并行下载
                if download_tasks:
                    results = await asyncio.gather(*download_tasks, return_exceptions=True)
                    for ex, ok in zip(download_examples_list, results):
                        if ok is not True:
                            failed_image_count += 1
            else:
                # 串行下载
                for ex in example_objs:
                    # 先保存元数据
                    examples_dicts.append(example_to_dict(ex))
                    
                    # 下载图片
                    if ex.filename and ex.url:
                        save_path = base_path / ex.filename
                        ok = await download_file(ex.url, save_path, app_settings.civitai.timeout)
                        if not ok:
                            failed_image_count += 1
                    else:
                        failed_image_count += 1
        else:
            # 不下载图片，只保存元数据
            for ex in example_objs:
                examples_dicts.append(example_to_dict(ex))
        
        # upsert 到数据库
        with DatabaseSession() as db:
            existing = db.get(ModelMetaTable, model_meta.version_id)
            now = datetime.now()
            
            if existing:
                # 更新现有记录
                existing.filename = model_meta.filename
                existing.name = model_meta.name
                existing.version = model_meta.version
                existing.desc = model_meta.desc
                existing.model_id = model_meta.model_id
                existing.type = model_meta.type
                existing.ecosystem = model_meta.ecosystem
                existing.base_model = model_meta.base_model
                existing.sha256 = model_meta.sha256
                existing.trained_words = list(model_meta.trained_words or [])
                existing.url = model_meta.url
                existing.web_page_url = model_meta.web_page_url
                existing.examples = examples_dicts
                existing.preference = getattr(model_meta, 'preference', 'neutral')
                existing.updated_at = now
                db.add(existing)
                db.commit()
                db.refresh(existing)
                db.expunge(existing)
                saved_table = existing
            else:
                # 创建新记录
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
                    trained_words=list(model_meta.trained_words or []),
                    url=model_meta.url,
                    web_page_url=model_meta.web_page_url,
                    examples=examples_dicts,
                    preference=getattr(model_meta, 'preference', 'neutral'),
                    created_at=now,
                    updated_at=now,
                )
                db.add(payload)
                db.commit()
                db.refresh(payload)
                db.expunge(payload)
                saved_table = payload

        logger.success(f"已保存模型元数据到数据库: {saved_table.name} ({saved_table.type})")
        # 转换为 Pydantic 模型返回
        saved_meta = ModelMeta.from_table(saved_table)
        return saved_meta, failed_image_count, total_image_count

    async def delete(self, model_meta: ModelMeta) -> bool:
        """删除模型元数据（不强制删除本地图片目录）。"""
        return await self.delete_by_id(model_meta.version_id)
    
    async def delete_by_id(self, version_id: int) -> bool:
        """通过 version_id 删除模型元数据。"""
        with DatabaseSession() as db:
            meta = db.get(ModelMetaTable, version_id)
            if not meta:
                return False
            db.delete(meta)
            db.commit()
            return True

    def set_preference(self, version_id: int, preference: str) -> Optional[ModelMeta]:
        """更新模型偏好。"""
        with DatabaseSession() as db:
            meta_table = db.get(ModelMetaTable, version_id)
            if not meta_table:
                return None
            meta_table.preference = preference
            meta_table.updated_at = datetime.now()
            db.add(meta_table)
            db.commit()
            db.refresh(meta_table)
            db.expunge(meta_table)
            return ModelMeta.from_table(meta_table)

    def get_all(self) -> List[ModelMeta]:
        """获取所有模型元数据。"""
        with DatabaseSession() as db:
            metas = db.exec(select(ModelMetaTable)).all()
            result = []
            for m in metas:
                db.expunge(m)
                result.append(ModelMeta.from_table(m))
            return result

    def update_fields(self, version_id: int, **fields) -> Optional[ModelMeta]:
        """更新任意字段后返回最新记录。"""
        with DatabaseSession() as db:
            meta_table = db.get(ModelMetaTable, version_id)
            if not meta_table:
                return None
            for k, v in fields.items():
                if hasattr(meta_table, k):
                    setattr(meta_table, k, v)
            meta_table.updated_at = datetime.now()
            db.add(meta_table)
            db.commit()
            db.refresh(meta_table)
            db.expunge(meta_table)
            return ModelMeta.from_table(meta_table)
    
    def clear_all(self) -> int:
        """清空所有模型元数据。"""
        with DatabaseSession() as db:
            statement = select(ModelMetaTable)
            metas = db.exec(statement).all()
            count = len(metas)
            for meta in metas:
                db.delete(meta)
            db.commit()
            logger.success(f"已清空所有模型元数据，共删除 {count} 个")
            return count


model_meta_db_service = ModelMetaDbService()
