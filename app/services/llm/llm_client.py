"""
LLM 客户端模块

基于 LangChain 1.0 的 LLM 封装
"""

from typing import Optional, List, Dict, Any, AsyncIterator
import os

from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.callbacks import CallbackManager
from langchain_core.outputs import LLMResult

from app.core.config import settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)


class LLMClient:
    """
    LLM 客户端封装类

    支持:
    - OpenAI GPT 系列模型
    - 可扩展支持其他模型（Azure, Anthropic 等）
    - 流式输出
    - 回调管理
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        callback_manager: Optional[CallbackManager] = None,
    ):
        """
        初始化 LLM 客户端

        Args:
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            api_key: API Key
            api_base: API Base URL
            callback_manager: 回调管理器
        """
        self.model = model or settings.llm.model
        self.temperature = temperature if temperature is not None else settings.llm.temperature
        self.max_tokens = max_tokens or settings.llm.max_tokens
        self.api_key = api_key or settings.llm.api_key or os.getenv("OPENAI_API_KEY", "")
        self.api_base = api_base or settings.llm.api_base or None
        self.callback_manager = callback_manager

        # 设置 LangSmith 追踪
        if settings.llm.langsmith_tracing:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = settings.llm.langsmith_project
            if settings.llm.langsmith_api_key:
                os.environ["LANGCHAIN_API_KEY"] = settings.llm.langsmith_api_key

        self._chat_model: Optional[BaseChatModel] = None

    @property
    def chat_model(self) -> BaseChatModel:
        """获取 Chat 模型"""
        if self._chat_model is None:
            self._chat_model = self._create_chat_model()
        return self._chat_model

    def _create_chat_model(self) -> BaseChatModel:
        """创建 Chat 模型"""
        provider = settings.llm.provider.lower()

        if provider == "openai":
            kwargs = {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "api_key": self.api_key,
                "timeout": settings.llm.request_timeout,
            }
            if self.api_base:
                kwargs["base_url"] = self.api_base
            if self.callback_manager:
                kwargs["callback_manager"] = self.callback_manager

            return ChatOpenAI(**kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> str:
        """
        对话

        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}]

        Returns:
            模型响应
        """
        langchain_messages = self._convert_messages(messages)
        response = await self.chat_model.ainvoke(langchain_messages, **kwargs)
        return response.content

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        流式对话

        Args:
            messages: 消息列表

        Yields:
            模型响应片段
        """
        langchain_messages = self._convert_messages(messages)
        async for chunk in self.chat_model.astream(langchain_messages, **kwargs):
            if chunk.content:
                yield chunk.content

    def chat_sync(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> str:
        """
        同步对话

        Args:
            messages: 消息列表

        Returns:
            模型响应
        """
        langchain_messages = self._convert_messages(messages)
        response = self.chat_model.invoke(langchain_messages, **kwargs)
        return response.content

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """转换消息格式"""
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    async def generate(
        self,
        prompt: str,
        **kwargs,
    ) -> str:
        """
        生成文本

        Args:
            prompt: 提示词

        Returns:
            生成的文本
        """
        return await self.chat([{"role": "user", "content": prompt}], **kwargs)


# 全局 LLM 客户端实例
llm_client = LLMClient()


def get_llm_client(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs,
) -> LLMClient:
    """
    获取 LLM 客户端

    Args:
        model: 模型名称
        temperature: 温度参数

    Returns:
        LLM 客户端实例
    """
    if model or temperature is not None or kwargs:
        return LLMClient(model=model, temperature=temperature, **kwargs)
    return llm_client


def get_chat_model(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs,
) -> BaseChatModel:
    """
    获取 LangChain Chat 模型

    Args:
        model: 模型名称
        temperature: 温度参数

    Returns:
        LangChain Chat 模型
    """
    client = get_llm_client(model=model, temperature=temperature, **kwargs)
    return client.chat_model
