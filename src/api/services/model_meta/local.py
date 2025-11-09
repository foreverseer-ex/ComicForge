"""
本地模型元数据组织者（local）。
从本地 SD-Forge 目录读取与缓存模型元数据。
"""
import asyncio
import shutil
from pathlib import Path
from typing import Optional

from loguru import logger

from api.schemas.model_meta import ModelMeta, Example
from api.services.model_meta.base import AbstractModelMetaService
from api.utils.path import checkpoint_meta_home, lora_meta_home
from api.utils.download import is_local_url, download_file
from api.settings import app_settings
from api.constants.model_meta import ModelType


class LocalModelModelMetaService(AbstractModelMetaService):
    """
    模型元数据管理器（本地）。

    - 负责扫描本地 SD‑Forge 模型目录并维护内存列表（Checkpoint/LoRA/VAE）。
    - 提供将远程模型元数据本地化的能力（下载示例图，转换URL）。
    - 序列化和读取本地元数据文件。
    """

    def __init__(self):
        """初始化模型元数据管理器。"""
        self.lora_list: list[ModelMeta] = []
        self.sd_list: list[ModelMeta] = []
        self.vae_list: list[ModelMeta] = []
        self.flush()

    def flush(self):
        """
        刷新所有模型元数据。
        
        从磁盘重新扫描并刷新内存缓存。
        适用于外部添加了新模型文件或元数据后，需要刷新服务状态的场景。
        """
        # 清空现有缓存
        self.lora_list.clear()
        self.sd_list.clear()
        self.vae_list.clear()
        
        # 重新加载
        self._flush_checkpoint_meta()
        self._flush_lora_meta()
        self._flush_vae()
    
    def clear_all(self) -> int:
        """
        清空所有模型元数据。
        
        删除本地存储的所有 Checkpoint 和 LoRA 元数据文件。
        
        :return: 删除的元数据数量
        """
        import shutil
        
        deleted_count = 0
        
        # 删除 Checkpoint 元数据
        if checkpoint_meta_home.exists():
            for meta_dir in checkpoint_meta_home.iterdir():
                if meta_dir.is_dir():
                    try:
                        shutil.rmtree(meta_dir)
                        deleted_count += 1
                        logger.debug(f"已删除 Checkpoint 元数据: {meta_dir.name}")
                    except Exception as e:
                        logger.exception(f"删除 Checkpoint 元数据失败 ({meta_dir}): {e}")
        
        # 删除 LoRA 元数据
        if lora_meta_home.exists():
            for meta_dir in lora_meta_home.iterdir():
                if meta_dir.is_dir():
                    try:
                        shutil.rmtree(meta_dir)
                        deleted_count += 1
                        logger.debug(f"已删除 LoRA 元数据: {meta_dir.name}")
                    except Exception as e:
                        logger.exception(f"删除 LoRA 元数据失败 ({meta_dir}): {e}")
        
        # 清空内存缓存
        self.lora_list.clear()
        self.sd_list.clear()
        self.vae_list.clear()
        
        logger.success(f"已清空所有模型元数据，共删除 {deleted_count} 个")
        return deleted_count

    def _flush_lora_meta(self):
        """
        刷新 LoRA 模型元数据（内部方法）。
        
        从 lora_meta_home 目录读取所有元数据文件，而不是从 safetensors 文件扫描。
        """
        if not lora_meta_home.exists():
            logger.debug(f"LoRA 元数据目录不存在: {lora_meta_home}")
            return
        
        loaded_count = 0
        # 遍历元数据目录中的所有子目录
        for meta_dir in lora_meta_home.iterdir():
            if not meta_dir.is_dir():
                continue
            
            metadata_file = meta_dir / "metadata.json"
            if not metadata_file.exists():
                logger.debug(f"元数据文件不存在: {metadata_file}")
                continue
            
            try:
                model_meta = ModelMeta.model_validate_json(
                    metadata_file.read_text(encoding='utf-8')
                )
                self.lora_list.append(model_meta)
                loaded_count += 1
            except Exception as e:
                logger.exception(f"加载 LoRA 元数据失败 ({metadata_file}): {e}")
                continue
        
        if loaded_count > 0:
            logger.debug(f"已加载 {loaded_count} 个 LoRA 元数据")

    def _flush_checkpoint_meta(self):
        """
        刷新 Checkpoint 模型元数据（内部方法）。
        
        从 checkpoint_meta_home 目录读取所有元数据文件，而不是从 safetensors 文件扫描。
        """
        if not checkpoint_meta_home.exists():
            logger.debug(f"Checkpoint 元数据目录不存在: {checkpoint_meta_home}")
            return
        
        loaded_count = 0
        # 遍历元数据目录中的所有子目录
        for meta_dir in checkpoint_meta_home.iterdir():
            if not meta_dir.is_dir():
                continue
            
            metadata_file = meta_dir / "metadata.json"
            if not metadata_file.exists():
                logger.debug(f"元数据文件不存在: {metadata_file}")
                continue
            
            try:
                model_meta = ModelMeta.model_validate_json(
                    metadata_file.read_text(encoding='utf-8')
                )
                self.sd_list.append(model_meta)
                loaded_count += 1
            except Exception as e:
                logger.exception(f"加载 Checkpoint 元数据失败 ({metadata_file}): {e}")
                continue
        
        if loaded_count > 0:
            logger.debug(f"已加载 {loaded_count} 个 Checkpoint 元数据")

    def _flush_vae(self):
        """刷新VAE模型元数据（预留，内部方法）。"""
        return

    def test(self) -> bool:
        """
        测试本地服务是否可用。
        
        本地服务始终可用。
        
        :return: True
        """
        return True
    
    @staticmethod
    async def _save_meta_to_disk(meta: ModelMeta):
        """
        将模型元数据序列化到磁盘（内部方法，异步版本）。
        
        :param meta: 模型元数据（必须包含 type 字段）
        """
        import aiofiles
        
        home = checkpoint_meta_home if meta.type == ModelType.CHECKPOINT else lora_meta_home
        meta_file = home / Path(meta.filename).stem / 'metadata.json'
        
        # 异步创建目录（使用 asyncio.to_thread 包装同步操作）
        import asyncio
        await asyncio.to_thread(meta_file.parent.mkdir, parents=True, exist_ok=True)
        
        # 异步写入文件
        async with aiofiles.open(meta_file, 'w', encoding='utf-8') as f:
            await f.write(meta.model_dump_json(indent=2))
    
    async def save(self, model_meta: ModelMeta, parallel_download: bool = False) -> tuple[ModelMeta, int, int]:
        """
        将模型元数据本地化并保存。
        
        此方法会：
        1. 下载所有远程示例图片到本地
        2. 保持 example 的原始 URL（不替换为本地 file:// URL）
        3. 序列化 ModelMeta 到本地 metadata.json
        
        注意：示例图片的 URL 保持原始值（Civitai URL），实际文件保存在本地。
        前端获取图片时，应根据 version_id 和 filename 查找本地文件。
        
        :param model_meta: 模型元数据（必须包含 type 字段，可以是远程的或本地的）
        :param parallel_download: 是否并行下载示例图片，默认 False（串行下载）
        :return: (本地化后的 ModelMeta, 失败的图片数量, 总图片数量)
        """
        # 确定基础路径与重名处理（使用内存缓存匹配同名文件）
        home = checkpoint_meta_home if model_meta.type == ModelType.CHECKPOINT else lora_meta_home

        existing_meta = self.get_by_filename(model_meta.filename)
        if existing_meta is not None:
            # 同名已存在：若 AIR xi同则改名以区分
            if (existing_meta.air or "") != (model_meta.air or ""):
                filename=Path(model_meta.filename)
                model_meta.filename=f"{filename.stem}-{model_meta.model_id}-{model_meta.version_id}{filename.suffix}"


        base_path = home / Path(model_meta.filename).stem
        base_path.mkdir(parents=True, exist_ok=True)
        
        # 处理示例图片（支持串行或并行下载）
        localized_examples: list[Example] = []
        
        # 分离本地和远程的示例图片
        local_examples = []
        remote_examples = []
        for example in model_meta.examples:
            if is_local_url(example.url):
                local_examples.append(example)
            else:
                remote_examples.append(example)
        
        # 本地示例直接添加
        for example in local_examples:
            localized_examples.append(example)
            logger.debug(f"示例图片已是本地: {example.filename}")
        
        # 下载远程示例图片
        failed_image_count = 0
        total_image_count = len(remote_examples)
        
        if remote_examples:
            if parallel_download:
                # 并行下载
                logger.debug(f"并行下载 {len(remote_examples)} 张示例图片")
                download_tasks = []
                for example in remote_examples:
                    save_path = base_path / example.filename
                    download_tasks.append(
                        self._download_example_image(example, save_path)
                    )
                
                # 等待所有下载任务完成
                results = await asyncio.gather(*download_tasks, return_exceptions=True)
                
                # 处理下载结果
                for example, result in zip(remote_examples, results):
                    if isinstance(result, Exception):
                        logger.exception(f"下载示例图片失败 ({example.filename}): {result}")
                        failed_image_count += 1
                        continue
                    elif result:
                        # 下载成功，保持原始 URL（不替换为本地 file:// URL）
                        localized_examples.append(example)
                        logger.debug(f"成功下载示例图片: {example.filename}")
                    else:
                        failed_image_count += 1
                        logger.warning(f"下载失败，跳过示例图片: {example.filename}")
            else:
                # 串行下载（原有逻辑）
                logger.debug(f"串行下载 {len(remote_examples)} 张示例图片")
                for example in remote_examples:
                    save_path = base_path / example.filename
                    logger.debug(f"下载示例图片: {example.filename}")
                    
                    success = await download_file(example.url, save_path, app_settings.civitai.timeout)
                    if success:
                        # 下载成功，保持原始 URL（不替换为本地 file:// URL）
                        localized_examples.append(example)
                        logger.debug(f"成功下载示例图片: {example.filename}")
                    else:
                        failed_image_count += 1
                        # 下载失败，跳过这张图片（download_file 已经记录了警告日志）
                        logger.warning(f"下载失败，跳过示例图片: {example.filename}")

        # 创建本地化的 ModelMeta
        localized_meta = ModelMeta(
            filename=model_meta.filename,
            name=model_meta.name,
            version=model_meta.version,
            desc=model_meta.desc,
            model_id=model_meta.model_id,
            version_id=model_meta.version_id,
            type=model_meta.type,
            base_model=model_meta.base_model,
            sha256=model_meta.sha256,
            trained_words=model_meta.trained_words,
            url=model_meta.url,
            examples=localized_examples,
            ecosystem=model_meta.ecosystem,
            web_page_url=model_meta.web_page_url,
            air=model_meta.air,
        )
        
        # 保存元数据到本地
        await self._save_meta_to_disk(localized_meta)
        logger.success(f"已保存模型元数据: {model_meta.name} ({model_meta.type})")
        
        return localized_meta, failed_image_count, total_image_count
    
    async def _download_example_image(self, example: Example, save_path: Path) -> bool:
        """
        下载单个示例图片（内部方法，用于并行下载）。
        
        :param example: 示例图片对象
        :param save_path: 保存路径
        :return: 下载成功返回 True，失败返回 False
        """
        try:
            return await download_file(example.url, save_path, app_settings.civitai.timeout)
        except Exception as e:
            logger.exception(f"下载示例图片失败 ({example.filename}): {e}")
            return False
    
    async def delete(self, model_meta: ModelMeta) -> bool:
        """
        删除模型元数据及其关联的示例图片（异步版本）。
        
        此方法会：
        1. 删除元数据目录（包括 metadata.json 和所有示例图片）
        2. 从内存缓存中移除该模型
        
        :param model_meta: 要删除的模型元数据
        :return: 删除成功返回 True，失败返回 False
        """
        try:
            # 确定元数据目录
            if model_meta.type == ModelType.CHECKPOINT:
                meta_dir = checkpoint_meta_home / Path(model_meta.filename).stem
                cache_list = self.sd_list
            elif model_meta.type == ModelType.LORA:
                meta_dir = lora_meta_home / Path(model_meta.filename).stem
                cache_list = self.lora_list
            else:
                logger.error(f"不支持的模型类型: {model_meta.type}")
                return False
            
            # 异步删除目录（包括所有内容），使用线程池避免阻塞事件循环
            if meta_dir.exists():
                await asyncio.to_thread(shutil.rmtree, meta_dir)
                logger.info(f"已删除元数据目录: {meta_dir}")
            else:
                logger.warning(f"元数据目录不存在: {meta_dir}")
            
            # 从内存缓存中移除
            try:
                cache_list.remove(model_meta)
                logger.debug(f"已从缓存中移除: {model_meta.name}")
            except ValueError:
                logger.warning(f"模型不在缓存中: {model_meta.name}")
            
            logger.success(f"已删除模型元数据: {model_meta.name} ({model_meta.type})")
            return True
            
        except Exception as e:
            logger.exception(f"删除模型元数据失败: {model_meta.name}")
            return False
    
    # ==================== 实现基类接口 ====================
    
    def get_by_version_name(self, version_name: str) -> Optional[ModelMeta]:
        """
        通过模型版本名称获取模型元数据（从内存缓存）。
        
        :param version_name: 模型版本名称（如 "waiIllustriousSDXL-v150"）
        :return: 模型元数据，未找到返回 None
        """
        # 按 version_name 属性匹配
        for meta in self.sd_list + self.lora_list + self.vae_list:
            if meta.version_name == version_name:
                return meta
        
        logger.debug(f"未在缓存中找到版本名称对应的模型: {version_name}")
        return None
    
    def get_by_name(self, name: str) -> Optional[ModelMeta]:
        """
        通过模型名称获取模型元数据（从内存缓存）。
        
        :param name: 模型名称或文件名（不含扩展名）
        :return: 模型元数据，未找到返回 None
        """
        # 仅按展示名称精确匹配
        for meta in self.sd_list + self.lora_list + self.vae_list:
            if meta.name == name:
                return meta
        
        logger.debug(f"未在缓存中找到模型: {name}")
        return None

    def get_by_filename(self, filename: str) -> Optional[ModelMeta]:
        """
        通过文件名（stem）获取模型元数据（从内存缓存）。
        
        :param filename: 文件名或路径，支持包含扩展名
        :return: 模型元数据，未找到返回 None
        """
        name_stem = Path(filename).stem
        for meta in self.sd_list + self.lora_list + self.vae_list:
            if Path(meta.filename).stem == name_stem:
                return meta
        logger.debug(f"未在缓存中找到文件名对应的模型: {filename}")
        return None
    
    def get_by_path(self, path: Path) -> Optional[ModelMeta]:
        """
        通过模型文件路径获取模型元数据。
        
        从内存缓存中查找，如果未找到返回 None。
        注意：需要先调用 flush() 或确保服务已初始化。
        
        :param path: 模型文件路径
        :return: 模型元数据，未找到返回 None
        """
        if not path.exists():
            logger.warning(f"模型文件不存在: {path}")
            return None
        
        # 从缓存中查找（使用文件名查找）
        filename = path.stem  # 去掉 .safetensors 后缀
        meta = self.get_by_name(filename)
        
        if meta is None:
            logger.debug(f"未找到元数据: {filename}")
        
        return meta
    
    def get_by_hash(self, file_hash: str) -> Optional[ModelMeta]:
        """
        通过模型文件哈希值获取模型元数据（仅从本地缓存）。
        
        :param file_hash: SHA-256 哈希值
        :return: 模型元数据，未找到返回 None
        """
        # 在所有已加载的模型中搜索
        for meta in self.sd_list + self.lora_list + self.vae_list:
            if meta.sha256.lower() == file_hash.lower():
                return meta
        
        logger.debug(f"未找到哈希值为 {file_hash} 的模型")
        return None
    
    def get_by_id(self, version_id: int) -> Optional[ModelMeta]:
        """
        通过 Civitai 模型版本 ID 获取模型元数据（仅从本地缓存）。
        
        :param version_id: Civitai 模型版本 ID
        :return: 模型元数据，未找到返回 None
        """
        # 在本地缓存中查找
        for meta in self.sd_list + self.lora_list + self.vae_list:
            if meta.version_id == version_id:
                return meta
        
        logger.debug(f"未找到版本 ID 为 {version_id} 的模型")
        return None
    
    async def set_preference(self, version_id: int, preference: str) -> Optional[ModelMeta]:
        """
        设置模型的偏好状态。
        
        :param version_id: Civitai 模型版本 ID
        :param preference: 偏好状态（'liked', 'neutral', 'disliked'）
        :return: 更新后的模型元数据，未找到返回 None
        """
        # 验证偏好值
        if preference not in ['liked', 'neutral', 'disliked']:
            raise ValueError(f"无效的偏好值: {preference}，必须是 'liked', 'neutral' 或 'disliked'")
        
        # 在本地缓存中查找
        meta = None
        for m in self.sd_list + self.lora_list + self.vae_list:
            if m.version_id == version_id:
                meta = m
                break
        
        if meta is None:
            logger.warning(f"未找到版本 ID 为 {version_id} 的模型")
            return None
        
        # 更新内存缓存
        meta.preference = preference
        
        # 保存到磁盘
        await self._save_meta_to_disk(meta)
        
        logger.info(f"已设置模型偏好状态: {meta.name} (version_id={version_id}, preference={preference})")
        return meta


local_model_meta_service = LocalModelModelMetaService()
