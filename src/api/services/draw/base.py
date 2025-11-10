"""
绘图服务基础抽象类。

定义所有绘图服务的统一接口。
"""
from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image

from api.schemas.draw import DrawArgs


class AbstractDrawService(ABC):
    """
    绘图服务抽象基类。
    
    定义统一的绘图接口，支持不同的后端（SD-Forge、Civitai 等）。
    """
    
    @abstractmethod
    def draw(self, args: DrawArgs, name: str | None = None, desc: str | None = None) -> str:
        """
        创建单个绘图任务并启动监控。
        
        :param args: 绘图参数
        :param name: 任务名称（可选）
        :param desc: 任务描述（可选）
        :return: job_id
        """
        raise NotImplementedError
    
    def batch_from_jobs(self, job_ids: list[str]) -> str:
        """
        从多个 job_id 组合成一个 batch（通用方法）。
        
        :param job_ids: job_id 列表
        :return: batch_id
        """
        from datetime import datetime
        from api.schemas.draw import BatchJob
        from api.services.db import BatchJobService
        
        batch_job = BatchJobService.create(BatchJob(
            job_ids=job_ids,
            created_at=datetime.now()
        ))
        return batch_job.batch_id
    
    def draw_batch(self, args: DrawArgs, batch_size: int = 1, name: str | None = None, desc: str | None = None) -> str:
        """
        批量创建绘图任务并组成 batch（通用方法）。
        
        :param args: 绘图参数
        :param batch_size: 批量大小
        :param name: 任务名称（可选）
        :param desc: 任务描述（可选）
        :return: batch_id
        """
        job_ids = []
        for i in range(batch_size):
            job_id = self.draw(args, name=name, desc=desc)
            job_ids.append(job_id)
        
        return self.batch_from_jobs(job_ids)
    
    @abstractmethod
    async def get_job_status(self, job_id: str) -> bool:
        """
        获取任务状态（异步）。
        
        :param job_id: 任务 ID
        :return: 是否完成
        """
        raise NotImplementedError
    
    @abstractmethod
    async def get_image(self, job_id: str) -> Image.Image:
        """
        获取生成的图片（异步）。
        
        :param job_id: 任务 ID
        :return: PIL Image 对象
        """
        raise NotImplementedError
    
    @abstractmethod
    async def save_image(self, job_id: str, save_path: str | Path) -> None:
        """
        保存生成的图片到文件（异步）。
        
        :param job_id: 任务 ID
        :param save_path: 保存路径
        """
        raise NotImplementedError

