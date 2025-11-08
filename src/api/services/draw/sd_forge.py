"""
SD-Forge 绘图服务实现。
"""
from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Optional, Dict, Any

import httpx
from PIL import Image
from loguru import logger

from api.settings import app_settings
from api.schemas.draw import DrawArgs
from .base import AbstractDrawService


class SdForgeDrawService(AbstractDrawService):
    """
    SD-Forge（Stable Diffusion WebUI）绘图服务。
    
    - base_url：sd-forge/sd-webui 服务地址，默认 http://127.0.0.1:7860
    - 功能：获取模型列表、读取/设置 options、调用 txt2img 生成。
    """

    def __init__(self):
        """初始化服务。"""
        self._jobs: dict[str, dict[str, Any]] = {}  # 存储任务信息 {job_id: result}

    @staticmethod
    def _get_loras() -> Dict[str, Any]:
        """
        获取 LoRA 模型列表（/sdapi/v1/loras）。
        
        :return: LoRA 模型列表
        """
        url = f"{app_settings.sd_forge.base_url}/sdapi/v1/loras"
        with httpx.Client(timeout=app_settings.sd_forge.timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _get_sd_models() -> Dict[str, Any]:
        """
        获取 SD 模型列表（/sdapi/v1/sd-models）。
        
        :return: SD 模型列表
        """
        url = f"{app_settings.sd_forge.base_url}/sdapi/v1/sd-models"
        with httpx.Client(timeout=app_settings.sd_forge.timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _get_options() -> Dict[str, Any]:
        """
        获取 SD 模型选项（/sdapi/v1/options）。
        
        :return: SD 模型选项
        """
        url = f"{app_settings.sd_forge.base_url}/sdapi/v1/options"
        with httpx.Client(timeout=app_settings.sd_forge.timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _set_options(
        sd_model_checkpoint: str | None = None,
        sd_vae: str | None = None,
    ) -> None:
        """
        切换 SD 模型（/sdapi/v1/options）。
        
        :param sd_model_checkpoint: 模型检查点，来自 /sdapi/v1/sd-models 的 title 字段
        :param sd_vae: VAE 模型，来自 /sdapi/v1/options 的 sd_vae 字段
        """
        url = f"{app_settings.sd_forge.base_url}/sdapi/v1/options"
        payload = {}
        if sd_model_checkpoint:
            payload["sd_model_checkpoint"] = sd_model_checkpoint
        if sd_vae:
            payload["sd_vae"] = sd_vae
        with httpx.Client(timeout=app_settings.sd_forge.timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()

    def _create_text2image(
        self,
        prompt: str,
        negative_prompt: str = "",
        loras: Optional[Dict[str, float]] = None,
        styles: list[str] = (),
        seed: int = -1,
        sampler: str = 'DPM++ 2M Karras',
        steps: int = 30,
        cfg_scale: float = 7.0,
        width: int = 1024,
        height: int = 1024,
        clip_skip: int | None = None,
        save_images: bool = True,
    ) -> Dict[str, Any]:
        """
        文生图（/sdapi/v1/txt2img）。
        
        :return: 包含 images、parameters 等字段的响应
        """
        # 处理 LoRA：分离正面和负面 LoRA
        final_prompt = prompt
        final_negative_prompt = negative_prompt or ""
        
        if loras:
            positive_tags = []
            negative_tags = []
            for name, weight in loras.items():
                if weight < 0:
                    # 负数权重表示负面 LoRA，正化后添加到负面提示词
                    negative_tags.append(f"<lora:{name}:{abs(weight)}>")
                else:
                    # 正数权重表示正面 LoRA，添加到正向提示词
                    positive_tags.append(f"<lora:{name}:{weight}>")
            
            if positive_tags:
                final_prompt = " ".join(positive_tags) + " " + (prompt or "")
            if negative_tags:
                final_negative_prompt = " ".join(negative_tags) + " " + (negative_prompt or "")

        payload: Dict[str, Any] = {
            "prompt": final_prompt,
            "negative_prompt": final_negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "n_iter": 1,
            "batch_size": 1,
            # 保存策略：保存单图、不保存网格
            "save_images": bool(save_images),
            "do_not_save_grid": True,
            "do_not_save_samples": not bool(save_images),
            # 响应返回图片
            "send_images": True,
        }
        
        if sampler:
            payload["sampler_name"] = sampler
        payload["seed"] = seed
        if styles:
            payload["styles"] = list(styles)
        # 映射 clip_skip 到 webui 的 CLIP_stop_at_last_layers
        if clip_skip is not None:
            payload["CLIP_stop_at_last_layers"] = clip_skip

        url = f"{app_settings.sd_forge.base_url}/sdapi/v1/txt2img"
        with httpx.Client(timeout=app_settings.sd_forge.generate_timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

    # ========== 实现抽象接口 ==========

    def draw(self, args: DrawArgs, batch_size: int = 1, name: str | None = None, desc: str | None = None) -> str:
        """
        批量创建绘图任务并启动监控。
        
        注意：如果指定了model和vae，会自动检查当前选项，如果不同则设置。
        model 和 vae 参数应该是 version_name，需要通过模型元数据服务查找对应的 SD-Forge title。
        
        :param args: 绘图参数（model 和 vae 是 version_name）
        :param batch_size: 批量大小
        :param name: 任务名称（可选）
        :param desc: 任务描述（可选）
        :return: batch_id
        """
        from api.services.model_meta import local_model_meta_service
        from api.services.db import JobService, BatchJobService
        from api.schemas.draw import Job, BatchJob
        from datetime import datetime
        from api.utils.path import jobs_home
        import asyncio
        
        job_ids = []
        
        # 创建 batch_size 个 job
        draw_args_dict = args.model_dump(exclude_none=True)
        if 'loras' not in draw_args_dict:
            draw_args_dict['loras'] = {}
        
        for i in range(batch_size):
            # 创建 Job 记录（ID 会自动生成）
            job = Job(
                name=name,
                desc=desc,
                created_at=datetime.now(),
                status="pending",
                draw_args=draw_args_dict,
                data={}
            )
            job = JobService.create(job)
            job_ids.append(job.job_id)
            
            # 启动后台任务：执行绘图并监控
            asyncio.create_task(self._draw_and_monitor_job_async(job.job_id, args))
        
        # 创建 BatchJob 记录（ID 会自动生成）
        batch_job = BatchJob(
            job_ids=job_ids,
            created_at=datetime.now()
        )
        batch_job = BatchJobService.create(batch_job)
        
        logger.success(f"批量创建任务完成: batch_id={batch_job.batch_id}, job_count={len(job_ids)}")
        return batch_job.batch_id

    async def _draw_and_monitor_job_async(self, job_id: str, args: DrawArgs) -> None:
        """
        执行绘图并监控任务（后台任务）。
        
        :param job_id: 本地 job_id（UUID）
        :param args: 绘图参数
        """
        from api.services.model_meta import local_model_meta_service
        from api.services.db import JobService
        from api.utils.path import jobs_home
        from datetime import datetime
        
        try:
            # SD-Forge 是同步的，直接执行
            # 注意：这里需要调用旧的同步 draw 方法，但我们需要重构它
            # 暂时先使用旧的逻辑
            
            # 如果指定了 model 或 vae，先检查当前选项，如果不同则设置
            if args.model or args.vae:
                current_options = self._get_options()
                need_update = False
                update_kwargs = {}
                
                # 检查 model
                if args.model:
                    model_meta = local_model_meta_service.get_by_version_name(args.model)
                    if not model_meta:
                        raise RuntimeError(f"未找到模型元数据: {args.model}")
                    
                    sd_models = self._get_sd_models()
                    sd_model_title = None
                    for sd_model in sd_models:
                        from pathlib import Path
                        sd_model_filename_stem = Path(sd_model.get('title', '')).stem
                        if Path(model_meta.filename).stem == sd_model_filename_stem:
                            sd_model_title = sd_model.get('title')
                            break
                    
                    if not sd_model_title:
                        raise RuntimeError(f"未在 SD-Forge 中找到模型: {args.model} (filename: {model_meta.filename})")
                    
                    current_model = current_options.get("sd_model_checkpoint", "")
                    if current_model != sd_model_title:
                        update_kwargs["sd_model_checkpoint"] = sd_model_title
                        need_update = True
                
                # 检查 vae
                if args.vae:
                    vae_meta = local_model_meta_service.get_by_version_name(args.vae)
                    if not vae_meta:
                        raise RuntimeError(f"未找到 VAE 元数据: {args.vae}")
                    
                    from pathlib import Path
                    vae_filename_stem = Path(vae_meta.filename).stem
                    current_vae = current_options.get("sd_vae", "")
                    if current_vae != vae_filename_stem:
                        update_kwargs["sd_vae"] = vae_filename_stem
                        need_update = True
                
                if need_update:
                    self._set_options(**update_kwargs)
            
            # 转换 LoRAs
            loras_for_sd_forge: Dict[str, float] = {}
            if args.loras:
                for lora_version_name, strength in args.loras.items():
                    lora_meta = local_model_meta_service.get_by_version_name(lora_version_name)
                    if not lora_meta:
                        logger.warning(f"未找到 LoRA 元数据: {lora_version_name}，跳过")
                        continue
                    from pathlib import Path
                    lora_filename_stem = Path(lora_meta.filename).stem
                    loras_for_sd_forge[lora_filename_stem] = strength
            
            # 调用 SD-Forge API
            result = self._create_text2image(
                prompt=args.prompt,
                negative_prompt=args.negative_prompt,
                loras=loras_for_sd_forge,
                seed=args.seed,
                sampler=args.sampler,
                steps=args.steps,
                cfg_scale=args.cfg_scale,
                width=args.width,
                height=args.height,
                clip_skip=args.clip_skip,
                save_images=True,
            )
            
            # 保存图片
            images = result.get("images", [])
            if images:
                job_image_path = jobs_home / f"{job_id}.png"
                import base64
                import aiofiles
                img_base64 = images[0]
                img_bytes = base64.b64decode(img_base64)
                job_image_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(job_image_path, 'wb') as f:
                    await f.write(img_bytes)
                logger.success(f"任务图像已保存: {job_id} -> {job_image_path}")
            
            # 标记任务完成
            JobService.update(job_id, completed_at=datetime.now(), status="completed")
            
        except Exception as e:
            logger.exception(f"SD-Forge 绘图失败: job_id={job_id}, error={e}")
            JobService.update(job_id, status="failed", completed_at=datetime.now())

    async def get_job_status(self, job_id: str) -> bool:
        """
        获取任务状态（异步）。
        
        :param job_id: 任务 ID
        :return: 是否完成
        """
        # SD-Forge 的状态检查是内存操作，不需要异步，但为了接口一致性使用 async
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"任务不存在: {job_id}")
        return job.get("completed", False)

    async def get_image(self, job_id: str) -> Image.Image:
        """
        获取生成的图片（异步）。
        
        :param job_id: 任务 ID
        :return: PIL Image 对象
        """
        # SD-Forge 的图片获取是内存操作，不需要异步，但为了接口一致性使用 async
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"任务不存在: {job_id}")
        
        if not job.get("completed"):
            raise RuntimeError(f"任务未完成: {job_id}")
        
        result = job.get("result", {})
        images = result.get("images", [])
        
        if not images:
            raise RuntimeError(f"任务无图片结果: {job_id}")
        
        # SD-Forge 返回的是 base64 编码的图片
        img_base64 = images[0]
        img_bytes = base64.b64decode(img_base64)
        img = Image.open(io.BytesIO(img_bytes))
        
        return img

    async def save_image(self, job_id: str, save_path: str | Path) -> None:
        """
        保存生成的图片到文件（异步）。
        
        :param job_id: 任务 ID
        :param save_path: 保存路径
        """
        import aiofiles
        
        img = await self.get_image(job_id)
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用 aiofiles 异步保存图片
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        async with aiofiles.open(save_path, 'wb') as f:
            await f.write(img_bytes.read())
        
        logger.info(f"图片已保存: {save_path}")


# 全局单例
sd_forge_draw_service = SdForgeDrawService()
