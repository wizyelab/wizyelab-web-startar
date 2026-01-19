"""
Agent 记忆模块

提供不同类型的对话记忆
"""

from typing import Optional, List, Dict, Any

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
)

from app.core.config import settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)


class InMemoryChatHistory(BaseChatMessageHistory):
    """
    内存中的对话历史

    用于存储单个会话的对话历史
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._messages: List[BaseMessage] = []

    @property
    def messages(self) -> List[BaseMessage]:
        """获取所有消息"""
        return self._messages

    def add_message(self, message: BaseMessage) -> None:
        """添加消息"""
        self._messages.append(message)
        logger.debug(f"Message added to session {self.session_id}: {type(message).__name__}")

    def add_user_message(self, message: str) -> None:
        """添加用户消息"""
        self.add_message(HumanMessage(content=message))

    def add_ai_message(self, message: str) -> None:
        """添加 AI 消息"""
        self.add_message(AIMessage(content=message))

    def clear(self) -> None:
        """清空消息"""
        self._messages = []
        logger.debug(f"Session {self.session_id} cleared")


class ConversationMemory:
    """
    对话记忆管理器

    支持多种记忆类型:
    - buffer: 完整对话缓存
    - buffer_window: 滑动窗口缓存
    - summary: 摘要记忆
    """

    def __init__(
        self,
        memory_type: Optional[str] = None,
        memory_k: Optional[int] = None,
        llm=None,
    ):
        """
        初始化对话记忆

        Args:
            memory_type: 记忆类型 (buffer, buffer_window, summary)
            memory_k: 窗口大小（仅 buffer_window 模式）
            llm: LLM 实例（仅 summary 模式需要）
        """
        self.memory_type = memory_type or settings.agent.memory_type
        self.memory_k = memory_k or settings.agent.memory_k
        self.llm = llm
        self._memory = self._create_memory()

    def _create_memory(self):
        """创建记忆实例"""
        if self.memory_type == "buffer":
            return ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history",
            )
        elif self.memory_type == "buffer_window":
            return ConversationBufferWindowMemory(
                k=self.memory_k,
                return_messages=True,
                memory_key="chat_history",
            )
        elif self.memory_type == "summary":
            if self.llm is None:
                raise ValueError("LLM is required for summary memory")
            return ConversationSummaryMemory(
                llm=self.llm,
                return_messages=True,
                memory_key="chat_history",
            )
        else:
            raise ValueError(f"Unknown memory type: {self.memory_type}")

    @property
    def memory(self):
        """获取记忆实例"""
        return self._memory

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """保存对话上下文"""
        self._memory.save_context(inputs, outputs)

    def load_memory_variables(self, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """加载记忆变量"""
        return self._memory.load_memory_variables(inputs or {})

    def clear(self) -> None:
        """清空记忆"""
        self._memory.clear()

    @property
    def chat_history(self) -> List[BaseMessage]:
        """获取对话历史"""
        return self._memory.chat_memory.messages


# 会话记忆存储
_session_memories: Dict[str, ConversationMemory] = {}


def get_memory(
    session_id: str = "default",
    memory_type: Optional[str] = None,
    memory_k: Optional[int] = None,
    llm=None,
    create_if_not_exists: bool = True,
) -> Optional[ConversationMemory]:
    """
    获取会话记忆

    Args:
        session_id: 会话 ID
        memory_type: 记忆类型
        memory_k: 窗口大小
        llm: LLM 实例
        create_if_not_exists: 如果不存在是否创建

    Returns:
        对话记忆实例
    """
    if session_id not in _session_memories:
        if create_if_not_exists:
            _session_memories[session_id] = ConversationMemory(
                memory_type=memory_type,
                memory_k=memory_k,
                llm=llm,
            )
        else:
            return None

    return _session_memories[session_id]


def delete_memory(session_id: str) -> bool:
    """
    删除会话记忆

    Args:
        session_id: 会话 ID

    Returns:
        是否删除成功
    """
    if session_id in _session_memories:
        del _session_memories[session_id]
        logger.info(f"Session memory deleted: {session_id}")
        return True
    return False


def clear_all_memories() -> None:
    """清空所有会话记忆"""
    _session_memories.clear()
    logger.info("All session memories cleared")
