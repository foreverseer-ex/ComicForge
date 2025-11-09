"""
Civitai 绘图服务实现。
"""


import asyncio
import io
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, TypeVar

import httpx
from PIL import Image
from loguru import logger

from api.schemas.draw import DrawArgs
from api.schemas.draw import Job, BatchJob
from api.services.db import JobService, BatchJobService
from api.settings import app_settings
from api.utils.path import jobs_home
from api.utils.retry import retry_async
from api.utils.timeout import with_timeout_async
from .base import AbstractDrawService

T = TypeVar('T')

# 在导入 civitai 之前设置环境变量
if app_settings.civitai.api_token:
    os.environ["CIVITAI_API_TOKEN"] = app_settings.civitai.api_token

import civitai
from civitai.api_config import HTTPException as CivitaiHTTPException


class CivitaiDrawService(AbstractDrawService):
    """
    Civitai 绘图服务。
    
    注意：对于 Civitai，job_id 实际上是 token。
    """

    # SD-Forge sampler 名称到 Civitai scheduler 名称的映射
    SCHEDULER_MAP = {
        # Euler 系列
        "Euler a": "EulerA",
        "Euler": "Euler",
        # DPM++/DPM2 系列映射到文档允许的 DPM2 家族
        "DPM++ 2M Karras": "DPM2MKarras",
        "DPM++ SDE Karras": "DPMSDEKarras",
        "DPM++ 2S a": "DPM2SA",
        "DPM++ 2M": "DPM2M",
        "DPM++ SDE": "DPMSDE",
        "DPM++ 2S a Karras": "DPM2SAKarras",
        # 其他调度器
        "DPM fast": "DPMFast",
        "DPM adaptive": "DPMAdaptive",
        "LMS": "LMS",
        "LMS Karras": "LMSKarras",
        "Heun": "Heun",
        "DPM2": "DPM2",
        "DPM2 a": "DPM2A",
        "DPM2 Karras": "DPM2Karras",
        "DPM2 a Karras": "DPM2AKarras",
        # 直映射支持（如有）
        "DDIM": "DDIM",
        "PLMS": "PLMS",
        "UniPC": "UniPC",
        "LCM": "LCM",
        "DDPM": "DDPM",
        "DEIS": "DEIS",
    }

    @classmethod
    def _map_sampler_to_scheduler(cls, sampler: str) -> str:
        """
        将 SD-Forge sampler 名称映射到 Civitai scheduler 名称。
        
        :param sampler: SD-Forge sampler 名称（如 "Euler a"）
        :return: Civitai scheduler 名称（如 "EulerA"）
        """
        return cls.SCHEDULER_MAP.get(sampler, "EulerA")  # 默认使用 EulerA

    def __init__(self):
        """初始化 Civitai 绘图服务，确保 API Token 已设置。"""
        # 确保环境变量已设置（如果 token 在初始化后被更新）
        if app_settings.civitai.api_token:
            os.environ["CIVITAI_API_TOKEN"] = app_settings.civitai.api_token

        # 注意：civitai 库内部使用 httpx，但库的 API 设计不支持直接传入超时参数
        # 我们会在每次调用时通过 asyncio.wait_for 来应用超时设置
        # 这样可以确保使用我们配置的 timeout 值

    async def _get_job_async(self, token: str) -> Dict[str, Any]:
        """
        查询任务状态（异步版本）。
        
        :param token: 任务 token
        :return: Civitai 的完整响应
        """

        async def _do_get():
            try:
                # 在异步上下文中，直接调用 civitai.jobs.get
                coro_or_task = civitai.jobs.get(token=token)

                # 检查返回值类型
                if isinstance(coro_or_task, dict):
                    # 如果直接返回字典，直接返回
                    return coro_or_task
                elif isinstance(coro_or_task, asyncio.Task):
                    # 如果是 Task，使用 asyncio.wait_for 应用超时
                    return await asyncio.wait_for(coro_or_task, timeout=app_settings.civitai.timeout)
                else:
                    # 如果是协程，使用 asyncio.wait_for 应用超时
                    return await asyncio.wait_for(coro_or_task, timeout=app_settings.civitai.timeout)

            except asyncio.TimeoutError:
                # asyncio.wait_for 超时
                logger.debug(f"civitai.jobs.get 超时（超时时间: {app_settings.civitai.timeout}秒）: {token}")
                raise httpx.ReadTimeout(f"请求超时（{app_settings.civitai.timeout}秒）")
            except (httpx.ReadTimeout, httpx.TimeoutException) as e:
                # 超时异常向上传播，由调用者处理
                logger.debug(f"civitai.jobs.get 超时: {e}")
                raise
            except Exception as e:
                logger.exception(f"civitai.jobs.get 调用失败: {e}")
                raise

        # 使用重试机制
        return await retry_async(
            _do_get,
            max_attempts=app_settings.civitai.retry_count,
            delay=app_settings.civitai.retry_delay,
            exceptions=(httpx.ReadTimeout, httpx.TimeoutException, httpx.ConnectTimeout, httpx.ConnectError),
            operation_name=f"查询 Civitai 任务状态 ({token})"
        )

    # ========== 辅助方法 ==========

    def _convert_args_to_civitai_format(self, args: DrawArgs) -> Dict[str, Any]:
        """
        将 DrawArgs 转换为 Civitai API 格式。
        
        :param args: 绘图参数
        :return: 包含 model_air, prompt, negative_prompt, scheduler, steps, cfg_scale, width, height, seed, clip_skip, positive_lora_airs, vae_air 的字典
        """
        from api.services.model_meta import model_meta_db_service

        # 获取模型的 AIR 标识符
        model_meta = model_meta_db_service.get_by_version_name(args.model)
        if not model_meta:
            raise RuntimeError(f"未找到模型: {args.model}")

        model_air = model_meta.air
        logger.debug(f"模型 AIR: {model_air}")

        # 转换 LoRAs 名称为 AIR（仅保留正向权重，忽略负向）
        positive_lora_airs: Dict[str, float] = {}
        if args.loras:
            for lora_name, strength in args.loras.items():
                lora_meta = model_meta_db_service.get_by_version_name(lora_name)
                if not lora_meta:
                    logger.warning(f"未找到 LoRA 元数据: {lora_name}，跳过")
                    continue
                if strength is None or strength <= 0:
                    # 暂不支持负向 LoRA，忽略非正值
                    logger.warning(f"忽略非正向 LoRA 权重: {lora_name} -> {strength}")
                    continue
                positive_lora_airs[lora_meta.air] = float(strength)
                logger.debug(f"LoRA AIR: {lora_meta.air}, strength: {strength}")

        # 转换 VAE 名称为 AIR
        vae_air: Optional[str] = None
        if args.vae:
            vae_meta = model_meta_db_service.get_by_version_name(args.vae)
            if vae_meta:
                vae_air = vae_meta.air
                logger.debug(f"VAE AIR: {vae_air}")

        # 负向 LoRA 不再拼接到负面提示，保持原始 negative_prompt
        final_negative_prompt = args.negative_prompt or ""

        # 验证宽高
        width = args.width
        height = args.height
        if width < 1 or height < 1:
            raise ValueError(f"宽度和高度必须大于 0: {width}x{height}")
        if width > 1024 or height > 1024:
            raise ValueError(f"宽高超过 Civitai API 限制（最大 1024）: {width}x{height}")

        payload = {
            "model_air": model_air,
            "prompt": args.prompt,
            "negative_prompt": final_negative_prompt,
            "scheduler": self._map_sampler_to_scheduler(args.sampler),
            "steps": args.steps,
            "cfg_scale": args.cfg_scale,
            "width": width,
            "height": height,
            "seed": args.seed,
            "clip_skip": args.clip_skip or 2,
            "positive_lora_airs": positive_lora_airs,
            "vae_air": vae_air,
            "ecosystem": model_meta.ecosystem,
        }
        try:
            import json
            logger.debug(f"[Civitai] civitai_params (after convert): {json.dumps(payload, ensure_ascii=False)}")
        except Exception:
            logger.debug(f"[Civitai] civitai_params (after convert): {payload}")
        return payload

    async def _create_job_token_async(self, civitai_params: Dict[str, Any]) -> str:
        """
        异步创建 Civitai 任务并返回 token（带重试）。
        
        :param civitai_params: Civitai API 参数（来自 _convert_args_to_civitai_format）
        :return: Civitai job token
        """

        async def _do_create():
            result = await self._create_text2image_async(**civitai_params)
            token = result.get("token")
            if not token:
                raise RuntimeError("Civitai 未返回 token")
            return token

        # 使用重试机制
        return await retry_async(
            _do_create,
            max_attempts=app_settings.civitai.retry_count,
            delay=app_settings.civitai.retry_delay,
            exceptions=(httpx.ReadTimeout, httpx.TimeoutException, httpx.ConnectTimeout, httpx.ConnectError),
            operation_name="创建 Civitai 任务"
        )

    async def _monitor_job_async(self, job_id: str, civitai_token: str) -> None:
        """
        监控 Civitai 任务直到完成，然后下载并保存图像。
        
        :param job_id: 本地 job_id（UUID）
        :param civitai_token: Civitai job token
        """
        timeout_seconds = app_settings.civitai.draw_timeout
        check_interval = 1.0  # 每秒检查一次

        async def _monitor():
            max_attempts = int(timeout_seconds / check_interval)
            attempt = 0

            while attempt < max_attempts:
                try:
                    # 检查任务状态
                    is_complete = await self.get_job_status(civitai_token)

                    if is_complete:
                        # 任务完成，下载并保存图像
                        job_image_path = jobs_home / f"{job_id}.png"
                        await self.save_image(civitai_token, job_image_path)
                        logger.success(f"任务图像已保存: {job_id} -> {job_image_path}")

                        # 标记任务完成
                        JobService.update(job_id, completed_at=datetime.now(), status="completed")
                        return

                    # 等待后重试
                    await asyncio.sleep(check_interval)
                    attempt += 1

                except Exception as e:
                    logger.exception(f"监控任务出错 (attempt {attempt}): {e}")
                    await asyncio.sleep(check_interval)
                    attempt += 1

            # 超时，标记为失败
            logger.error(f"任务超时: job_id={job_id}, timeout={timeout_seconds}秒")
            JobService.update(job_id, completed_at=datetime.now(), status="failed")

        # 使用超时机制包装监控函数
        try:
            await with_timeout_async(_monitor, timeout_seconds + 10, f"监控任务 {job_id}")
        except TimeoutError:
            logger.error(f"监控任务超时: job_id={job_id}")
            JobService.update(job_id, completed_at=datetime.now(), status="failed")

    async def _create_text2image_async(
            self,
            *,
            model_air: str,
            prompt: str,
            negative_prompt: str = "",
            scheduler: str = "EulerA",
            steps: int = 25,
            cfg_scale: float = 7.0,
            width: int = 512,
            height: int = 768,
            seed: int = -1,
            clip_skip: int = 2,
            positive_lora_airs: Optional[Dict[str, float]] = None,
            vae_air: Optional[str] = None,
            ecosystem: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        异步创建 Civitai 文生图任务，返回 { token }。
        
        :param model_air: 模型 AIR 标识符
        :param prompt: 提示词
        :param negative_prompt: 负提示词
        :param scheduler: 调度器
        :param steps: 推理步数
        :param cfg_scale: CFG 缩放因子
        :param width: 图像宽度
        :param height: 图像高度
        :param seed: 随机种子
        :param clip_skip: CLIP 层跳过数
        :param positive_lora_airs: 正面 LoRA 字典
        :param vae_air: VAE AIR 标识符
        :return: 包含 token 的字典
        """
        option: Dict[str, Any] = {
            "model": model_air,
            "params": {
                "prompt": prompt,
                "negativePrompt": negative_prompt,
                "scheduler": scheduler,
                "steps": steps,
                "cfgScale": cfg_scale,
                "width": width,
                "height": height,
                "seed": seed,
                "clipSkip": clip_skip,
            },
        }

        # 不再设置 baseModel，避免 civitai 库的 FromTextSchema 校验报 "Extra inputs are not permitted"

        # 处理 additionalNetworks（LoRA 和 VAE）使用字典结构
        additional: Dict[str, Any] = {}

        # 添加正面 LoRA
        for air, strength in positive_lora_airs.items():
            additional[air] = {"type": "Lora", "strength": float(strength)}

        # 添加 VAE
        if vae_air:
            additional[vae_air] = {"type": "VAE", "strength": 1.0}

        if additional:
            option["additionalNetworks"] = additional

        try:
            import json
            logger.debug("[Civitai] SDK request option (about to send): " + json.dumps(option, ensure_ascii=False))
        except Exception:
            logger.debug(f"[Civitai] SDK request option (about to send): {option}")

        # 调用 Civitai API（异步），若 400 则去除 additionalNetworks 重试一次
        async def _do_create_with_fallback():
            try:
                return await civitai.image.create(option)
            except CivitaiHTTPException as e:
                logger.warning(f"Civitai 返回 {e.status_code}，准备去掉 additionalNetworks 重试一次")
                # 去掉 additionalNetworks 后重试
                option_fallback = {**option}
                option_fallback.pop("additionalNetworks", None)
                try:
                    import json
                    logger.debug("[Civitai] SDK fallback option (no additionalNetworks): " + json.dumps(option_fallback, ensure_ascii=False))
                except Exception:
                    logger.debug(f"[Civitai] SDK fallback option (no additionalNetworks): {option_fallback}")
                try:
                    return await civitai.image.create(option_fallback)
                except Exception as e2:
                    logger.warning(f"SDK 再次失败，尝试使用 httpx 直接创建任务: {e2}")
                    # 直接请求 Civitai 接口作为兜底
                    job_input = {
                        "$type": "textToImage",
                        "model": model_air,
                        "params": option_fallback.get("params", {}),
                    }
                    url = "https://civitai.com/api/v1/consumer/jobs"
                    headers = {}
                    if app_settings.civitai.api_token:
                        headers["Authorization"] = f"Bearer {app_settings.civitai.api_token}"
                    async with httpx.AsyncClient(timeout=app_settings.civitai.timeout) as client:
                        resp = await client.post(url, json=job_input, params={"wait": "false"}, headers=headers)
                        try:
                            resp.raise_for_status()
                        except httpx.HTTPStatusError as he:
                            logger.error(f"Civitai 直连创建失败: {he.response.status_code} {he.response.text}")
                            raise
                        data = resp.json()
                        # 兼容 token 字段
                        token = data.get("token") or data.get("job", {}).get("token")
                        if not token:
                            logger.error(f"Civitai 返回无 token: {data}")
                            raise RuntimeError("Civitai 未返回 token")
                        return {"token": token}

        # 使用超时机制
        return await with_timeout_async(
            _do_create_with_fallback,
            timeout_seconds=app_settings.civitai.timeout,
            operation_name="创建 Civitai 绘图任务"
        )

    # ========== 实现抽象接口 ==========

    def draw(self, args: DrawArgs, batch_size: int = 1, name: Optional[str] = None, desc: Optional[str] = None) -> str:
        """
        批量创建绘图任务并启动监控。
        
        :param args: 绘图参数
        :param batch_size: 批量大小
        :param name: 任务名称（可选）
        :param desc: 任务描述（可选）
        :return: batch_id
        """
        # 1. 转换参数为 Civitai 格式
        civitai_params = self._convert_args_to_civitai_format(args)


        job_ids = []

        # 3. 创建 batch_size 个 job
        draw_args_dict = args.model_dump(exclude_none=True)
        if 'loras' not in draw_args_dict:
            draw_args_dict['loras'] = {}

        for i in range(batch_size):



            # 创建 Job 记录

            job=JobService.create(Job(

                name=name,
                desc=desc,
                created_at=datetime.now(),
                status="pending",
                draw_args=draw_args_dict,
                data={}
            ))
            job_ids.append(job.job_id)
            # 启动后台任务：创建 token 并监控
            asyncio.create_task(self._create_and_monitor_job_async(job.job_id, civitai_params))

        # 4. 创建 BatchJob 记录

        batch_job=BatchJobService.create(BatchJob(
            job_ids=job_ids,
            created_at=datetime.now()
        ))

        logger.success(f"批量创建任务完成: batch_id={batch_job.batch_id}, job_count={len(job_ids)}")
        return batch_job.batch_id

    async def _create_and_monitor_job_async(self, job_id: str, civitai_params: Dict[str, Any]) -> None:
        """
        创建 Civitai 任务 token 并启动监控（后台任务）。
        
        :param job_id: 本地 job_id（UUID）
        :param civitai_params: Civitai API 参数
        """
        try:
            # 1. 创建 token（带重试）
            civitai_token = await self._create_job_token_async(civitai_params)

            # 2. 更新 job.data
            job = JobService.get(job_id)
            if job:
                data = job.data or {}
                data['civitai_job_token'] = civitai_token
                JobService.update(job_id, data=data)
                logger.success(f"Civitai 任务已创建并绑定: job_id={job_id}, token={civitai_token}")
            else:
                logger.error(f"未找到 Job: {job_id}")
                return

            # 3. 启动监控任务
            await self._monitor_job_async(job_id, civitai_token)

        except Exception as e:
            logger.exception(f"创建或监控 Civitai 任务失败: job_id={job_id}, error={e}")
            JobService.update(job_id, status="failed", completed_at=datetime.now())

    async def get_job_status(self, job_id: str) -> bool:
        """
        获取任务状态。
        
        :param job_id: 任务 ID（对于 Civitai 来说，这应该是 civitai_job_token）
        :return: 是否完成
        """
        try:
            # 在异步上下文中调用 _get_job_async
            # 注意：job_id 参数实际上是 civitai_job_token
            resp = await self._get_job_async(job_id)
            jobs = resp.get("jobs", [])

            if not jobs:
                return False

            # 检查第一个 job 的状态
            job = jobs[0]
            result = job.get("result")

            if not result:
                return False

            # result 可能是字典或列表
            # 如果是列表，取第一个元素；如果是字典，直接使用
            if isinstance(result, list):
                if not result:
                    return False
                result = result[0]

            # 检查是否有可用的结果
            available = result.get("available", False)
            return available

        except (httpx.ReadTimeout, httpx.TimeoutException) as e:
            # 超时不算错误，只是任务还没完成，返回 False 继续等待
            logger.debug(f"查询 Civitai 任务状态超时（任务可能还在处理中）: {job_id}")
            return False
        except Exception as e:
            logger.exception(f"查询 Civitai 任务状态失败: {e}")
            return False

    async def get_image(self, job_id: str) -> Image.Image:
        """
        获取生成的图片（异步）。
        
        :param job_id: 任务 ID（对于 Civitai 来说，这应该是 civitai_job_token）
        :return: PIL Image 对象
        """
        # 注意：job_id 参数实际上是 civitai_job_token
        resp = await self._get_job_async(job_id)
        jobs = resp.get("jobs", [])

        if not jobs:
            raise RuntimeError(f"任务无结果: {job_id}")

        job = jobs[0]
        result = job.get("result")

        if not result:
            raise RuntimeError(f"任务无结果: {job_id}")

        # result 可能是字典或列表
        # 如果是列表，取第一个元素；如果是字典，直接使用
        if isinstance(result, list):
            if not result:
                raise RuntimeError(f"任务无结果: {job_id}")
            result = result[0]

        if not result.get("available"):
            raise RuntimeError(f"任务未完成: {job_id}")

        # 获取图片 URL
        blob_url = result.get("blobUrl")
        if not blob_url:
            raise RuntimeError(f"任务无图片 URL: {job_id}")

        # 使用异步 HTTP 客户端下载图片
        async with httpx.AsyncClient(timeout=app_settings.civitai.timeout) as client:
            resp = await client.get(blob_url)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content))

        return img

    async def save_image(self, job_id: str, save_path: str | Path) -> None:
        """
        保存生成的图片到文件（异步）。
        
        :param job_id: 任务 ID（对于 Civitai 来说，这应该是 civitai_job_token）
        :param save_path: 保存路径
        """
        import aiofiles

        # 注意：job_id 参数实际上是 civitai_job_token
        img = await self.get_image(job_id)
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用 aiofiles 异步保存图片
        # PIL Image.save() 是同步的，但我们可以将图片数据先保存到内存，然后异步写入
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        async with aiofiles.open(save_path, 'wb') as f:
            await f.write(img_bytes.read())

        logger.info(f"图片已保存: {save_path}")


# 全局单例
civitai_draw_service = CivitaiDrawService()
