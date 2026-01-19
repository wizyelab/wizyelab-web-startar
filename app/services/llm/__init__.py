"""LLM 服务模块"""

from .agent import (
    WizyelabAgent,
    AgentType,
    create_agent,
    get_agent,
    delete_agent,
)
from .chains import (
    create_conversation_chain,
    create_qa_chain,
    create_rag_chain,
    create_structured_output_chain,
    create_product_recommendation_chain,
)
from .tools import (
    BaseTool,
    SearchTool,
    CalculatorTool,
    ProductSearchTool,
    VideoAnalysisTool,
    get_default_tools,
    get_tools_by_names,
)
from .memory import (
    ConversationMemory,
    InMemoryChatHistory,
    get_memory,
    delete_memory,
    clear_all_memories,
)
from .llm_client import (
    LLMClient,
    llm_client,
    get_llm_client,
    get_chat_model,
)

__all__ = [
    # Agent
    "WizyelabAgent",
    "AgentType",
    "create_agent",
    "get_agent",
    "delete_agent",
    # Chains
    "create_conversation_chain",
    "create_qa_chain",
    "create_rag_chain",
    "create_structured_output_chain",
    "create_product_recommendation_chain",
    # Tools
    "BaseTool",
    "SearchTool",
    "CalculatorTool",
    "ProductSearchTool",
    "VideoAnalysisTool",
    "get_default_tools",
    "get_tools_by_names",
    # Memory
    "ConversationMemory",
    "InMemoryChatHistory",
    "get_memory",
    "delete_memory",
    "clear_all_memories",
    # LLM Client
    "LLMClient",
    "llm_client",
    "get_llm_client",
    "get_chat_model",
]
