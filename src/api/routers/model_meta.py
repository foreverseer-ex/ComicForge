"""
模型元数据相关的路由。

提供从 Civitai 导入模型元数据和获取模型示例图片的功能。
"""
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from api.services.model_meta import civitai_model_meta_service, local_model_meta_service
from api.services.draw.sd_forge import SdForgeDrawService
from api.utils.civitai import AIR
from api.utils.download import url_to_path
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


class ImportModelResponse(BaseModel):
    """导入单个模型的响应"""
    success: bool
    air: str
    model_name: Optional[str] = None
    error: Optional[str] = None


class BatchImportModelRequest(BaseModel):
    """批量导入模型的请求"""
    airs: List[str]


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
        
        # 从 Civitai 获取模型元数据
        model_meta = await civitai_model_meta_service.get_by_id(air.version_id)
        if not model_meta:
            return ImportModelResponse(
                success=False,
                air=request.air,
                error=f"未找到版本 ID: {air.version_id}"
            )
        
        # 保存到本地（包括下载示例图片，串行下载）
        saved_meta = await civitai_model_meta_service.save(model_meta)
        if not saved_meta:
            return ImportModelResponse(
                success=False,
                air=request.air,
                error="保存模型元数据失败"
            )
        
        # 刷新本地缓存（在线程池中执行，避免阻塞）
        await asyncio.to_thread(local_model_meta_service.flush)
        
        logger.success(f"导入成功: {saved_meta.name} ({request.air})")
        return ImportModelResponse(
            success=True,
            air=request.air,
            model_name=saved_meta.name
        )
        
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
    max_concurrency = app_settings.civitai.max_concurrency
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def import_with_semaphore(air: str) -> ImportModelResponse:
        """使用信号量控制的导入函数"""
        async with semaphore:
            return await import_model(ImportModelRequest(air=air))
    
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
    
    Returns:
        LoRA 元数据列表，每个项包含：
        - name: LoRA 名称
        - alias: LoRA 别名
        - filename: 文件名
        - available: 是否在绘图后端可用（仅当后端为 sd_forge 时检查）
        - 其他元数据字段
    """
    try:
        # 获取本地 LoRA 元数据
        lora_metas = local_model_meta_service.lora_list
        
        # 如果绘图后端是 SD-Forge，检查可用性
        sd_forge_loras = set()
        if app_settings.draw.backend == "sd_forge":
            try:
                sd_loras_data = SdForgeDrawService._get_loras()  # pylint: disable=protected-access
                if isinstance(sd_loras_data, list):
                    sd_forge_loras = {lora.get("name") for lora in sd_loras_data if lora.get("name")}
            except Exception as e:
                logger.warning(f"无法获取 SD-Forge LoRA 列表: {e}")
        
        # 构建返回列表
        result = []
        for lora in lora_metas:
            lora_dict = lora.model_dump()
            # 手动添加 version_name 和 air（因为它们是 @property，不会自动序列化）
            lora_dict["version_name"] = lora.version_name
            lora_dict["air"] = lora.air
            # 如果后端是 SD-Forge，标记可用性
            if app_settings.draw.backend == "sd_forge":
                # SD-Forge 中的 LoRA 名称通常是去掉扩展名的文件名
                lora_filename_no_ext = Path(lora.filename).stem
                lora_dict["available"] = lora_filename_no_ext in sd_forge_loras or lora.filename in sd_forge_loras
            else:
                # Civitai 后端，所有都可用
                lora_dict["available"] = True
            
            result.append(lora_dict)
        
        return result
    except Exception as e:
        logger.exception(f"获取 LoRA 元数据失败: {e}")
        return []


@router.get("/checkpoint", summary="获取本地 Checkpoint 元数据列表")
async def get_checkpoints() -> List[Dict[str, Any]]:
    """
    获取本地模型元数据中的 Checkpoint 列表。
    
    Returns:
        Checkpoint 元数据列表，每个项包含：
        - name: 模型名称
        - filename: 文件名
        - available: 是否在绘图后端可用（仅当后端为 sd_forge 时检查）
        - 其他元数据字段
    """
    try:
        # 获取本地 Checkpoint 元数据
        checkpoint_metas = local_model_meta_service.sd_list
        
        # 如果绘图后端是 SD-Forge，检查可用性
        sd_forge_models = set()
        if app_settings.draw.backend == "sd_forge":
            try:
                sd_models_data = SdForgeDrawService._get_sd_models()  # pylint: disable=protected-access
                if isinstance(sd_models_data, list):
                    sd_forge_models = {model.get("title") for model in sd_models_data if model.get("title")}
                    # 也添加 model_name
                    sd_forge_models.update({model.get("model_name") for model in sd_models_data if model.get("model_name")})
            except Exception as e:
                logger.warning(f"无法获取 SD-Forge 模型列表: {e}")
        
        # 构建返回列表
        result = []
        for model in checkpoint_metas:
            model_dict = model.model_dump()
            # 手动添加 version_name 和 air（因为它们是 @property，不会自动序列化）
            model_dict["version_name"] = model.version_name
            model_dict["air"] = model.air
            # 如果后端是 SD-Forge，标记可用性
            if app_settings.draw.backend == "sd_forge":
                model_filename_no_ext = Path(model.filename).stem
                model_dict["available"] = (
                    model.name in sd_forge_models or 
                    model.filename in sd_forge_models or 
                    model_filename_no_ext in sd_forge_models
                )
            else:
                # Civitai 后端，所有都可用
                model_dict["available"] = True
            
            result.append(model_dict)
        
        return result
    except Exception as e:
        logger.exception(f"获取 Checkpoint 元数据失败: {e}")
        return []


# ==================== 图片端点 ====================

@router.get("/image", summary="获取模型示例图片")
async def get_model_image(image_url: str) -> FileResponse:
    """
    获取模型示例图片。
    
    通过图片 URL（file:// URL 或相对路径）获取图片文件。
    
    Args:
        image_url: 图片 URL，例如 "file:///C:/path/to/image.jpg" 或相对路径 "checkpoint/model_name/example.jpg"
    
    Returns:
        图片文件响应
    
    实现要点：
    - 支持 file:// URL 和相对路径
    - 只允许访问 model_meta 目录下的文件
    - 防止路径遍历攻击
    """
    from api.utils.path import checkpoint_meta_home, lora_meta_home
    from api.utils.download import url_to_path
    
    try:
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
            
            # 返回文件
            return FileResponse(
                path=file_path,
                media_type="image/jpeg"  # 可以根据文件扩展名设置更准确的类型
            )
        else:
            raise HTTPException(status_code=404, detail=f"图片不存在: {image_url}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取图片失败: {image_url}")
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")
