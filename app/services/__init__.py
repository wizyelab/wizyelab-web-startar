"""服务模块

注意：LLM 相关模块使用懒加载，避免影响其他服务
"""

__all__ = [
    # Agent
    "WizyelabAgent",
    "create_agent",
    "get_agent",
    # Chains
    "create_conversation_chain",
    "create_qa_chain",
    # Memory
    "get_memory",
    "ConversationMemory",
]


def __getattr__(name):
    """懒加载 LLM 相关模块"""
    if name in __all__:
        from .llm import (
            WizyelabAgent,
            create_agent,
            get_agent,
            create_conversation_chain,
            create_qa_chain,
            get_memory,
            ConversationMemory,
        )
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
