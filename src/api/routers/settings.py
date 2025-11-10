"""
设置管理的路由。

提供应用配置的读取和更新功能。
设置包括：LLM、绘图、Civitai、SD Forge 等子系统的配置。
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body
from loguru import logger
from pydantic import BaseModel

from api.settings import app_settings, AppSettings
from api.settings.llm_setting import LlmSettings
from api.settings.draw_setting import DrawSettings
from api.settings.civitai_setting import CivitaiSettings
from api.settings.sd_forge_setting import SdForgeSettings
from api.constants.llm import DEFAULT_SYSTEM_PROMPT

router = APIRouter(
    prefix="/settings",
    tags=["设置管理"],
    responses={404: {"description": "设置不存在"}},
)


# ==================== 请求/响应模型 ====================

class SettingsUpdateRequest(BaseModel):
    """兼容占位：后续不再在路由中使用此模型"""
    llm: Dict[str, Any] | None = None
    draw: Dict[str, Any] | None = None
    civitai: Dict[str, Any] | None = None
    sd_forge: Dict[str, Any] | None = None


# ==================== 设置读取 ====================

@router.get("/", summary="获取所有设置")
async def get_settings() -> AppSettings:
    """
    获取所有应用设置。
    
    Returns:
        完整的应用设置对象，包含所有子系统的配置
    """
    return app_settings


@router.get("/llm", summary="获取 LLM 设置")
async def get_llm_settings() -> LlmSettings:
    """获取 LLM（大语言模型）配置"""
    return app_settings.llm


@router.get("/draw", summary="获取绘图设置")
async def get_draw_settings() -> DrawSettings:
    """获取绘图服务配置"""
    return app_settings.draw


@router.get("/civitai", summary="获取 Civitai 设置")
async def get_civitai_settings() -> CivitaiSettings:
    """获取 Civitai 服务配置"""
    return app_settings.civitai


@router.get("/sd-forge", summary="获取 SD Forge 设置")
async def get_sd_forge_settings() -> SdForgeSettings:
    """获取 SD Forge 服务配置"""
    return app_settings.sd_forge


# ==================== 设置更新 ====================

@router.put("/llm", summary="更新 LLM 设置")
async def update_llm_settings(settings: Dict[str, Any] = Body(...)) -> LlmSettings:
    """
    更新 LLM 设置。
    
    Args:
        settings: LLM 设置的字典，只包含要更新的字段
    
    Returns:
        更新后的 LLM 设置对象
    
    实现要点：
    - 使用 Pydantic 的 model_validate 来部分更新
    - 自动保存到配置文件
    - 更新全局 app_settings 实例
    """
    try:
        # 获取当前设置并转换为字典
        current_dict = app_settings.llm.model_dump()
        # 更新字典（只更新提供的字段）
        current_dict.update(settings)
        # 验证并创建新的设置对象
        new_llm_settings = LlmSettings(**current_dict)
        # 更新全局设置
        app_settings.llm = new_llm_settings
        # 保存到配置文件
        if app_settings.save(reason="更新 LLM 设置"):
            logger.info("LLM 设置已更新并保存")
        else:
            logger.warning("LLM 设置已更新，但保存到文件失败")
        
        return new_llm_settings
    except Exception as e:
        logger.exception(f"更新 LLM 设置失败: {e}")
        raise HTTPException(status_code=400, detail=f"更新 LLM 设置失败: {str(e)}")


@router.put("/draw", summary="更新绘图设置")
async def update_draw_settings(settings: Dict[str, Any] = Body(...)) -> DrawSettings:
    """
    更新绘图设置。
    
    Args:
        settings: 绘图设置的字典，只包含要更新的字段
    
    Returns:
        更新后的绘图设置对象
    """
    try:
        current_dict = app_settings.draw.model_dump()
        current_dict.update(settings)
        new_draw_settings = DrawSettings(**current_dict)
        app_settings.draw = new_draw_settings
        
        if app_settings.save(reason="更新绘图设置"):
            logger.info("绘图设置已更新并保存")
        else:
            logger.warning("绘图设置已更新，但保存到文件失败")
        
        return new_draw_settings
    except Exception as e:
        logger.exception(f"更新绘图设置失败: {e}")
        raise HTTPException(status_code=400, detail=f"更新绘图设置失败: {str(e)}")


@router.put("/civitai", summary="更新 Civitai 设置")
async def update_civitai_settings(settings: Dict[str, Any] = Body(...)) -> CivitaiSettings:
    """
    更新 Civitai 设置。
    
    Args:
        settings: Civitai 设置的字典，只包含要更新的字段
    
    Returns:
        更新后的 Civitai 设置对象
    """
    try:
        current_dict = app_settings.civitai.model_dump()
        current_dict.update(settings)
        new_civitai_settings = CivitaiSettings(**current_dict)
        app_settings.civitai = new_civitai_settings
        
        if app_settings.save(reason="更新 Civitai 设置"):
            logger.info("Civitai 设置已更新并保存")
        else:
            logger.warning("Civitai 设置已更新，但保存到文件失败")
        
        return new_civitai_settings
    except Exception as e:
        logger.exception(f"更新 Civitai 设置失败: {e}")
        raise HTTPException(status_code=400, detail=f"更新 Civitai 设置失败: {str(e)}")


@router.put("/sd-forge", summary="更新 SD Forge 设置")
async def update_sd_forge_settings(settings: Dict[str, Any] = Body(...)) -> SdForgeSettings:
    """
    更新 SD Forge 设置。
    
    Args:
        settings: SD Forge 设置的字典，只包含要更新的字段
    
    Returns:
        更新后的 SD Forge 设置对象
    """
    try:
        current_dict = app_settings.sd_forge.model_dump()
        current_dict.update(settings)
        new_sd_forge_settings = SdForgeSettings(**current_dict)
        app_settings.sd_forge = new_sd_forge_settings
        
        if app_settings.save(reason="更新 SD Forge 设置"):
            logger.info("SD Forge 设置已更新并保存")
        else:
            logger.warning("SD Forge 设置已更新，但保存到文件失败")
        
        return new_sd_forge_settings
    except Exception as e:
        logger.exception(f"更新 SD Forge 设置失败: {e}")
        raise HTTPException(status_code=400, detail=f"更新 SD Forge 设置失败: {str(e)}")


@router.put("/", summary="批量更新设置")
async def update_settings(
    llm: Dict[str, Any] | None = Body(None),
    draw: Dict[str, Any] | None = Body(None),
    civitai: Dict[str, Any] | None = Body(None),
    sd_forge: Dict[str, Any] | None = Body(None),
) -> Dict[str, Any]:
    """
    批量更新多个设置部分。
    
    Args:
        request: 包含要更新的设置部分的字典，每个部分都是可选的
    
    Returns:
        更新后的完整应用设置对象
    
    实现要点：
    - 支持同时更新多个设置部分
    - 只更新提供的部分，未提供的部分保持不变
    - 一次性保存所有更改
    """
    try:
        updated_sections = []
        
        # 更新 LLM 设置
        if llm is not None:
            current_dict = app_settings.llm.model_dump()
            current_dict.update(llm)
            app_settings.llm = LlmSettings(**current_dict)
            updated_sections.append("llm")
        
        # 更新绘图设置
        if draw is not None:
            current_dict = app_settings.draw.model_dump()
            current_dict.update(draw)
            app_settings.draw = DrawSettings(**current_dict)
            updated_sections.append("draw")
        
        # 更新 Civitai 设置
        if civitai is not None:
            current_dict = app_settings.civitai.model_dump()
            current_dict.update(civitai)
            app_settings.civitai = CivitaiSettings(**current_dict)
            updated_sections.append("civitai")
        
        # 更新 SD Forge 设置
        if sd_forge is not None:
            current_dict = app_settings.sd_forge.model_dump()
            current_dict.update(sd_forge)
            app_settings.sd_forge = SdForgeSettings(**current_dict)
            updated_sections.append("sd_forge")
        
        if updated_sections:
            # 保存到配置文件
            if app_settings.save(reason=f"批量更新设置: {', '.join(updated_sections)}"):
                logger.info(f"设置已更新并保存: {', '.join(updated_sections)}")
            else:
                logger.warning(f"设置已更新，但保存到文件失败: {', '.join(updated_sections)}")
        
        return app_settings
    except Exception as e:
        logger.exception(f"批量更新设置失败: {e}")
        raise HTTPException(status_code=400, detail=f"批量更新设置失败: {str(e)}")


@router.post("/reload", summary="重新加载设置")
async def reload_settings() -> AppSettings:
    """
    从配置文件重新加载设置。
    
    用于在手动修改 config.json 后，重新加载配置到内存。
    
    Returns:
        重新加载后的应用设置对象
    
    注意：
    - 这会覆盖当前内存中的设置
    - 如果有正在运行的服务（如 LLM），可能需要重启服务才能生效
    """
    try:
        # 重新加载配置并更新模块级别的全局变量
        import api.settings as settings_module
        settings_module.app_settings = AppSettings.load()
        
        # 更新当前模块导入的 app_settings 引用
        global app_settings
        app_settings = settings_module.app_settings
        
        logger.info("设置已重新加载")
        return app_settings
    except Exception as e:
        logger.exception(f"重新加载设置失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新加载设置失败: {str(e)}")


@router.post("/llm/reset-system-prompt", summary="重置系统提示词")
async def reset_system_prompt() -> Dict[str, str]:
    """
    重置 LLM 系统提示词为默认值。
    
    Returns:
        包含新系统提示词的字典
    """
    try:
        # 重置为默认值
        app_settings.llm.system_prompt = DEFAULT_SYSTEM_PROMPT
        
        # 保存到配置文件
        if app_settings.save(reason="重置系统提示词"):
            logger.info("系统提示词已重置为默认值并保存")
        else:
            logger.warning("系统提示词已重置，但保存到文件失败")
        
        return {"system_prompt": DEFAULT_SYSTEM_PROMPT}
    except Exception as e:
        logger.exception(f"重置系统提示词失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置系统提示词失败: {str(e)}")

