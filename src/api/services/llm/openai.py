"""
OpenAI 兼容 LLM 服务实现（支持 xAI/OpenAI/Anthropic/Google 等）。
"""

import httpx
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from loguru import logger

from api.settings import app_settings
from .base import AbstractLlmService


class OpenAILlmService(AbstractLlmService):
    """
    OpenAI 兼容的 LLM 服务。
    
    支持所有 OpenAI 兼容的 API 端点：
    - xAI (Grok)
    - OpenAI (GPT)
    - Anthropic (Claude)
    - Google (Gemini)
    - 自定义端点
    """

    def initialize_llm(self) -> bool:
        """
        初始化 OpenAI 兼容的 LLM 实例。
        
        :return: 初始化是否成功
        """
        try:
            # 创建带超时设置的 httpx 同步客户端
            # 注意：ChatOpenAI 的 http_client 参数需要同步客户端，不是异步客户端
            timeout = httpx.Timeout(
                app_settings.llm.timeout,
                connect=app_settings.llm.timeout,
                read=app_settings.llm.timeout,
                write=app_settings.llm.timeout,
                pool=app_settings.llm.timeout
            )
            http_client = httpx.Client(timeout=timeout)

            self.llm = ChatOpenAI(
                model=app_settings.llm.model,
                api_key=app_settings.llm.api_key,
                base_url=app_settings.llm.base_url,
                temperature=app_settings.llm.temperature,
                http_client=http_client,
            )
            logger.info(f"正在绑定 {len(self.tools)} 个工具到模型...")
            llm_with_tools = self.llm.bind_tools(self.tools)
            self.agent = create_agent(llm_with_tools, self.tools)
            logger.success(
                f"OpenAI 兼容服务初始化成功: {app_settings.llm.provider} / {app_settings.llm.model} "
                f"({len(self.tools)} 个工具)"
            )
            return True
        except Exception as e:
            logger.exception(f"OpenAI 兼容服务初始化失败: {e}")
            return False
