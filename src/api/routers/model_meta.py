"""
模型元数据相关的路由。

提供从 Civitai 导入模型元数据和获取模型示例图片的功能。
"""
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel
import httpx

from api.services.model_meta import civitai_model_meta_service, local_model_meta_service
from api.utils.civitai import AIR
from api.settings import app_settings

router = APIRouter(
    prefix="/model-meta",
    tags=["模型元数据管理"],
    responses={404: {"description": "资源不存在"}},
)


# ==================== 请求/响应模型 ====================

class ImportModelRequest(BaseModel):
    """导入单个模型的请求"""
    air: str
    download_images: bool = True  # 是否下载示例图片，默认 True
    parallel_download: bool = False  # 是否并行下载示例图片，默认 False（串行下载）


class ImportModelResponse(BaseModel):
    """导入单个模型的响应"""
    success: bool
    air: str
    model_name: Optional[str] = None
    error: Optional[str] = None
    skipped: bool = False  # 是否跳过（已存在）
    failed_image_count: int = 0  # 下载失败的图片数量
    total_image_count: int = 0  # 总图片数量


class BatchImportModelRequest(BaseModel):
    """批量导入模型的请求"""
    airs: List[str]
    download_images: bool = True  # 是否下载示例图片，默认 True


class BatchImportModelResponse(BaseModel):
    """批量导入模型的响应"""
    total: int
    success_count: int
    failed_count: int
    results: List[ImportModelResponse]


# ==================== 导入端点 ====================

@router.post("/import", response_model=ImportModelResponse, summary="导入单个模型")
async def import_model(request: ImportModelRequest) -> ImportModelResponse:
    """
    从 Civitai 导入单个模型元数据。
    
    此端点用于前端调用，导入完成后立即返回。
    前端可以通过并发调用多个此端点来实现批量导入。
    
    Args:
        request: 导入请求，包含 AIR 标识符
    
    Returns:
        导入结果，包含成功状态、模型名称或错误信息
    
    实现要点：
    - 解析 AIR 标识符
    - 从 Civitai 获取模型元数据
    - 保存到本地（包括下载示例图片）
    - 刷新本地缓存
    """
    try:
        # 解析 AIR 标识符
        air = AIR.parse(request.air)
        if not air:
            return ImportModelResponse(
                success=False,
                air=request.air,
                error=f"无效的 AIR 标识符: {request.air}"
            )
        
        logger.info(f"开始导入模型: {request.air} (version_id={air.version_id})")
        
        # 检查模型是否已存在（通过 version_id）
        existing_meta = local_model_meta_service.get_by_id(air.version_id)
        if existing_meta is not None:
            logger.info(f"模型已存在，跳过导入: {existing_meta.name} ({request.air})")
            return ImportModelResponse(
                success=True,
                air=request.air,
                model_name=existing_meta.name,
                skipped=True
            )
        
        # 从 Civitai 获取模型元数据
        try:
            model_meta = await civitai_model_meta_service.get_by_id(air.version_id)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException, httpx.ReadTimeout) as e:
            # 网络连接错误或超时
            error_msg = f"网络连接失败或请求超时，无法连接到 Civitai API。请检查网络连接或稍后重试。"
            logger.error(f"导入模型失败 ({request.air}): {error_msg} - {e}")
            return ImportModelResponse(
                success=False,
                air=request.air,
                error=error_msg
            )
        
        if not model_meta:
            return ImportModelResponse(
                success=False,
                air=request.air,
                error=f"未找到版本 ID: {air.version_id}"
            )
        
        # 保存到本地（包括下载示例图片，支持并行或串行下载）
        saved_meta, failed_image_count, total_image_count = await civitai_model_meta_service.save(
            model_meta, 
            download_images=request.download_images,
            parallel_download=request.parallel_download
        )
        if not saved_meta:
            return ImportModelResponse(
                success=False,
                air=request.air,
                error="保存模型元数据失败"
            )
        
        # 刷新本地缓存（在线程池中执行，避免阻塞）
        await asyncio.to_thread(local_model_meta_service.flush)
        
        logger.success(f"导入成功: {saved_meta.name} ({request.air})")
        
        # 构建响应，如果有图片下载失败，添加警告信息
        response = ImportModelResponse(
            success=True,
            air=request.air,
            model_name=saved_meta.name,
            failed_image_count=failed_image_count,
            total_image_count=total_image_count
        )
        
        # 如果有图片下载失败，在 error 字段中添加警告信息（但不影响 success 状态）
        if failed_image_count > 0:
            response.error = f"部分图片下载失败：{failed_image_count}/{total_image_count} 张图片未能下载"
        
        return response
        
    except Exception as e:
        logger.exception(f"导入模型失败 ({request.air}): {e}")
        return ImportModelResponse(
            success=False,
            air=request.air,
            error=str(e)
        )


@router.post("/batch-import", response_model=BatchImportModelResponse, summary="批量导入模型（测试用）")
async def batch_import_models(request: BatchImportModelRequest) -> BatchImportModelResponse:
    """
    批量导入多个模型元数据。
    
    此端点用于测试，会等待所有模型导入完成后才返回。
    
    Args:
        request: 批量导入请求，包含 AIR 标识符列表
    
    Returns:
        批量导入结果，包含总数、成功数、失败数和详细结果列表
    
    实现要点：
    - 遵循最大并发数设置
    - 使用信号量控制并发
    - 等待所有导入完成后返回
    """
    total = len(request.airs)
    success_count = 0
    failed_count = 0
    results: List[ImportModelResponse] = []
    
    # 创建信号量以控制并发数
    max_concurrency = app_settings.civitai.parallel_workers
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def import_with_semaphore(air: str) -> ImportModelResponse:
        """使用信号量控制的导入函数"""
        async with semaphore:
            return await import_model(ImportModelRequest(
                air=air,
                download_images=request.download_images
            ))
    
    logger.info(f"开始批量导入 {total} 个模型（最大并发数: {max_concurrency}）")
    
    try:
        # 并发导入所有模型（遵循最大并发数）
        results = await asyncio.gather(*[import_with_semaphore(air) for air in request.airs])
        
        # 统计结果
        for result in results:
            if result.success:
                success_count += 1
            else:
                failed_count += 1
        
        logger.success(f"批量导入完成: 成功 {success_count}, 失败 {failed_count}, 总计 {total}")
        
        return BatchImportModelResponse(
            total=total,
            success_count=success_count,
            failed_count=failed_count,
            results=results
        )
        
    except Exception as e:
        logger.exception(f"批量导入失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量导入失败: {str(e)}")


# ==================== 模型列表 API ====================

@router.get("/loras", summary="获取本地 LoRA 元数据列表")
async def get_loras() -> List[Dict[str, Any]]:
    """
    获取本地模型元数据中的 LoRA 列表。
    
    注意：此端点只返回本地缓存的模型元数据，不检查 SD-Forge 连接状态。
    模型是否在 SD-Forge 中可用，应该在生成图片时检查。
    
    Returns:
        LoRA 元数据列表，每个项包含：
        - name: LoRA 名称
        - alias: LoRA 别名
        - filename: 文件名
        - 其他元数据字段
    """
    try:
        # 获取本地 LoRA 元数据
        lora_metas = local_model_meta_service.lora_list
        
        # 构建返回列表
        result = []
        for lora in lora_metas:
            lora_dict = lora.model_dump()
            # 手动添加 version_name 和 air（因为它们是 @property，不会自动序列化）
            lora_dict["version_name"] = lora.version_name
            lora_dict["air"] = lora.air
            
            result.append(lora_dict)
        
        return result
    except Exception as e:
        logger.exception(f"获取 LoRA 元数据失败: {e}")
        return []


@router.get("/checkpoint", summary="获取本地 Checkpoint 元数据列表")
async def get_checkpoints() -> List[Dict[str, Any]]:
    """
    获取本地模型元数据中的 Checkpoint 列表。
    
    注意：此端点只返回本地缓存的模型元数据，不检查 SD-Forge 连接状态。
    模型是否在 SD-Forge 中可用，应该在生成图片时检查。
    
    Returns:
        Checkpoint 元数据列表，每个项包含：
        - name: 模型名称
        - filename: 文件名
        - 其他元数据字段
    """
    try:
        # 获取本地 Checkpoint 元数据
        checkpoint_metas = local_model_meta_service.sd_list
        
        # 构建返回列表
        result = []
        for model in checkpoint_metas:
            model_dict = model.model_dump()
            # 手动添加 version_name 和 air（因为它们是 @property，不会自动序列化）
            model_dict["version_name"] = model.version_name
            model_dict["air"] = model.air
            
            result.append(model_dict)
        
        return result
    except Exception as e:
        logger.exception(f"获取 Checkpoint 元数据失败: {e}")
        return []


# ==================== 图片端点 ====================

@router.get("/image", summary="获取模型示例图片")
async def get_model_image(
    image_url: str | None = None,
    version_id: int | None = None,
    filename: str | None = None
) -> FileResponse:
    """
    获取模型示例图片。
    
    支持两种方式：
    1. 通过 image_url（兼容旧方式，file:// URL 或相对路径）
    2. 通过 version_id 和 filename（推荐方式，根据模型版本ID和文件名查找本地文件）
    
    Args:
        image_url: 图片 URL（可选，兼容旧方式）
        version_id: 模型版本 ID（可选，新方式）
        filename: 示例图片文件名（可选，新方式）
    
    Returns:
        图片文件响应
    
    实现要点：
    - 优先使用 version_id + filename 方式（推荐）
    - 兼容旧的 image_url 方式
    - 只允许访问 model_meta 目录下的文件
    - 防止路径遍历攻击
    """
    from api.utils.path import checkpoint_meta_home, lora_meta_home
    from api.utils.download import url_to_path
    from pathlib import Path
    
    try:
        file_path: Path | None = None
        
        # 优先使用 version_id + filename 方式（推荐）
        if version_id is not None and filename:
            # 从本地缓存中查找模型
            model_meta = local_model_meta_service.get_by_id(version_id)
            if not model_meta:
                raise HTTPException(status_code=404, detail=f"未找到版本 ID 为 {version_id} 的模型")
            
            # 确定基础路径
            home = checkpoint_meta_home if model_meta.type == 'checkpoint' else lora_meta_home
            # 构建文件路径：data/model_meta/checkpoint或lora/模型名称/filename
            model_dir = home / Path(model_meta.filename).stem
            file_path = model_dir / filename
            
            # 验证文件存在
            if not file_path.exists() or not file_path.is_file():
                raise HTTPException(status_code=404, detail=f"图片不存在: {filename}")
            
            # 验证文件在允许的目录内（防止路径遍历）
            try:
                file_path.resolve().relative_to(home.resolve())
                is_allowed = True
            except ValueError:
                is_allowed = False
            
            if not is_allowed:
                raise HTTPException(status_code=403, detail="访问被拒绝")
        
        # 兼容旧的 image_url 方式
        elif image_url:
            # 尝试将 URL 转换为路径
            file_path = url_to_path(image_url)
            
            if file_path and file_path.exists() and file_path.is_file():
                # 验证文件在允许的目录内（防止路径遍历）
                try:
                    file_path.resolve().relative_to(checkpoint_meta_home.resolve())
                    is_allowed = True
                except ValueError:
                    try:
                        file_path.resolve().relative_to(lora_meta_home.resolve())
                        is_allowed = True
                    except ValueError:
                        is_allowed = False
                
                if not is_allowed:
                    raise HTTPException(status_code=403, detail="访问被拒绝")
            else:
                raise HTTPException(status_code=404, detail=f"图片不存在: {image_url}")
        else:
            raise HTTPException(status_code=400, detail="必须提供 image_url 或 (version_id + filename)")
        
        # 返回文件
        return FileResponse(
            path=file_path,
            media_type="image/jpeg"  # 可以根据文件扩展名设置更准确的类型
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取图片失败: {image_url or f'version_id={version_id}, filename={filename}'}")
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


# ==================== 删除端点 ====================

@router.delete("/{version_id}", summary="删除模型元数据")
async def delete_model(version_id: int) -> dict:
    """
    删除指定版本ID的模型元数据及其关联的示例图片。
    
    Args:
        version_id: Civitai 模型版本 ID（路径参数）
    
    Returns:
        删除结果，包含版本ID和模型名称
    
    Raises:
        404: 模型元数据不存在
    """
    try:
        # 从本地缓存中查找模型
        model_meta = local_model_meta_service.get_by_id(version_id)
        if not model_meta:
            raise HTTPException(status_code=404, detail=f"未找到版本 ID 为 {version_id} 的模型")
        
        # 删除模型元数据（异步删除，不会阻塞）
        success = await local_model_meta_service.delete(model_meta)
        if not success:
            raise HTTPException(status_code=500, detail="删除模型元数据失败")
        
        # 刷新本地缓存
        await asyncio.to_thread(local_model_meta_service.flush)
        
        logger.info(f"删除模型元数据成功: {model_meta.name} (version_id={version_id})")
        return {
            "version_id": version_id,
            "model_name": model_meta.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"删除模型元数据失败 (version_id={version_id}): {e}")
        raise HTTPException(status_code=500, detail=f"删除模型元数据失败: {str(e)}")


@router.post("/{version_id}/reset", summary="重置模型元数据（重新从 Civitai 下载）")
async def reset_model_meta(version_id: int, parallel_download: bool = False) -> Dict[str, Any]:
    """
    重置模型元数据，从 Civitai 重新下载元数据和示例图片。
    
    此端点用于重新下载模型元数据和图像，适用于图像下载失败的情况。
    会先删除现有的元数据，然后重新从 Civitai 获取并保存。
    
    Args:
        version_id: Civitai 模型版本 ID（路径参数）
        parallel_download: 是否并行下载示例图片，默认 False（串行下载）
    
    Returns:
        包含 version_id、model_name 和 success 状态的字典
    
    Raises:
        HTTPException: 模型不存在或重置失败时返回相应错误
    """
    try:
        # 检查模型是否存在
        existing_meta = local_model_meta_service.get_by_id(version_id)
        if not existing_meta:
            raise HTTPException(status_code=404, detail=f"未找到版本 ID 为 {version_id} 的模型")
        
        # 获取 AIR 标识符（如果存在）
        air_str = existing_meta.air if hasattr(existing_meta, 'air') and existing_meta.air else None
        
        logger.info(f"开始重置模型元数据: {existing_meta.name} (version_id={version_id})")
        
        # 删除现有模型元数据
        success = await local_model_meta_service.delete(existing_meta)
        if not success:
            logger.warning(f"删除现有模型元数据失败，继续尝试重新下载 (version_id={version_id})")
        
        # 从 Civitai 重新获取模型元数据
        try:
            model_meta = await civitai_model_meta_service.get_by_id(version_id)
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            error_msg = f"网络连接失败，无法连接到 Civitai API。请检查网络连接。"
            logger.error(f"重置模型失败 (version_id={version_id}): {error_msg} - {e}")
            raise HTTPException(status_code=502, detail=error_msg) from e
        except httpx.TimeoutException as e:
            error_msg = f"请求超时，无法从 Civitai API 获取数据。请稍后重试。"
            logger.error(f"重置模型失败 (version_id={version_id}): {error_msg} - {e}")
            raise HTTPException(status_code=504, detail=error_msg) from e
        
        if not model_meta:
            raise HTTPException(status_code=404, detail=f"未找到版本 ID: {version_id}")
        
        # 保存到本地（包括重新下载示例图片）
        saved_meta, failed_image_count, total_image_count = await civitai_model_meta_service.save(
            model_meta, 
            parallel_download=parallel_download
        )
        if not saved_meta:
            raise HTTPException(status_code=500, detail="保存模型元数据失败")
        
        # 刷新本地缓存
        await asyncio.to_thread(local_model_meta_service.flush)
        
        logger.success(f"重置成功: {saved_meta.name} (version_id={version_id})")
        
        result = {
            "version_id": version_id,
            "model_name": saved_meta.name,
            "success": True,
            "failed_image_count": failed_image_count,
            "total_image_count": total_image_count
        }
        
        # 如果有图片下载失败，添加警告信息
        if failed_image_count > 0:
            result["warning"] = f"部分图片下载失败：{failed_image_count}/{total_image_count} 张图片未能下载"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"重置模型元数据失败 (version_id={version_id}): {e}")
        raise HTTPException(status_code=500, detail=f"重置模型元数据失败: {str(e)}") from e


@router.patch("/{version_id}/preference", summary="设置模型偏好状态")
async def set_model_preference(version_id: int, preference: str) -> Dict[str, Any]:
    """
    设置模型的偏好状态。
    
    Args:
        version_id: Civitai 模型版本 ID（路径参数）
        preference: 偏好状态（查询参数，'liked', 'neutral', 'disliked'）
    
    Returns:
        包含 version_id、model_name 和 preference 状态的字典
    
    Raises:
        HTTPException: 模型不存在时返回 404，偏好值无效时返回 400
    """
    try:
        # 验证偏好值
        if preference not in ['liked', 'neutral', 'disliked']:
            raise HTTPException(
                status_code=400,
                detail=f"无效的偏好值: {preference}，必须是 'liked', 'neutral' 或 'disliked'"
            )
        
        meta = await local_model_meta_service.set_preference(version_id, preference)
        if not meta:
            raise HTTPException(status_code=404, detail=f"未找到版本 ID 为 {version_id} 的模型")
        
        return {
            "version_id": version_id,
            "model_name": meta.name,
            "preference": meta.preference
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"设置模型偏好状态失败 (version_id={version_id}): {e}")
        raise HTTPException(status_code=500, detail=f"设置模型偏好状态失败: {str(e)}")
