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
    def draw(self, args: DrawArgs, batch_size: int = 1, name: str | None = None, desc: str | None = None) -> str:
        """
        批量创建绘图任务并启动监控。
        
        :param args: 绘图参数
        :param batch_size: 批量大小
        :param name: 任务名称（可选）
        :param desc: 任务描述（可选）
        :return: batch_id（批次 ID）
        """
        raise NotImplementedError
    
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

