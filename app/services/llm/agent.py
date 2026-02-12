"""
Wizyelab Agent 模块

基于 LangChain 1.0 的 Agent 实现
"""

from typing import Optional, List, Dict, Any, AsyncIterator
from enum import Enum

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.callbacks import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from app.core.config import settings, PROJECT_DISPLAY_NAME
from app.services.llm.llm_client import get_chat_model
from app.services.llm.tools import get_default_tools, get_tools_by_names
from app.services.llm.memory import ConversationMemory, get_memory
from app.core.logging import setup_logger

logger = setup_logger(__name__)


class AgentType(str, Enum):
    """Agent 类型"""
    OPENAI_TOOLS = "openai_tools"
    REACT = "react"


# 默认系统提示
DEFAULT_SYSTEM_PROMPT = f"""你是 {PROJECT_DISPLAY_NAME} 智能运动助手，专注于帮助用户提升运动技能和选择合适的运动装备。

你的主要能力包括:
1. **装备推荐**: 根据用户的运动水平、预算和需求，推荐最合适的运动装备
2. **技术分析**: 分析用户的运动视频，提供技术改进建议
3. **知识问答**: 回答运动相关的专业问题
4. **进阶建议**: 为用户制定运动技能提升计划

在回答时，请:
- 提供专业、准确的信息
- 给出具体、可执行的建议
- 用友好、鼓励的语气交流
- 必要时使用工具获取最新信息

当前日期: {current_date}
"""


class WizyelabAgent:
    """
    Wizyelab 智能助手 Agent

    基于 LangChain 1.0 的 Agent 实现，支持:
    - 多种工具调用
    - 对话记忆
    - 流式输出
    - 回调管理
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[List[BaseTool]] = None,
        memory: Optional[ConversationMemory] = None,
        system_prompt: Optional[str] = None,
        agent_type: AgentType = AgentType.OPENAI_TOOLS,
        max_iterations: Optional[int] = None,
        verbose: Optional[bool] = None,
    ):
        """
        初始化 Wizyelab Agent

        Args:
            llm: LLM 实例
            tools: 工具列表
            memory: 记忆实例
            system_prompt: 系统提示
            agent_type: Agent 类型
            max_iterations: 最大迭代次数
            verbose: 是否输出详细信息
        """
        self.llm = llm or get_chat_model()
        self.tools = tools or get_default_tools()
        self.memory = memory
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.agent_type = agent_type
        self.max_iterations = max_iterations or settings.agent.max_iterations
        self.verbose = verbose if verbose is not None else settings.agent.verbose

        self._agent_executor: Optional[AgentExecutor] = None

    @property
    def agent_executor(self) -> AgentExecutor:
        """获取 Agent Executor"""
        if self._agent_executor is None:
            self._agent_executor = self._create_agent_executor()
        return self._agent_executor

    def _create_agent_executor(self) -> AgentExecutor:
        """创建 Agent Executor"""
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 创建 Agent
        if self.agent_type == AgentType.OPENAI_TOOLS:
            agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt,
            )
        else:
            raise ValueError(f"Unsupported agent type: {self.agent_type}")

        # 创建 Agent Executor
        executor_kwargs = {
            "agent": agent,
            "tools": self.tools,
            "verbose": self.verbose,
            "max_iterations": self.max_iterations,
            "early_stopping_method": settings.agent.early_stopping_method,
            "handle_parsing_errors": True,
        }

        if self.memory:
            executor_kwargs["memory"] = self.memory.memory

        return AgentExecutor(**executor_kwargs)

    async def chat(
        self,
        message: str,
        chat_history: Optional[List[BaseMessage]] = None,
        **kwargs,
    ) -> str:
        """
        异步对话

        Args:
            message: 用户消息
            chat_history: 对话历史
            **kwargs: 其他参数

        Returns:
            Agent 响应
        """
        from datetime import datetime

        inputs = {
            "input": message,
            "current_date": datetime.now().strftime("%Y-%m-%d"),
        }

        if chat_history:
            inputs["chat_history"] = chat_history

        try:
            result = await self.agent_executor.ainvoke(inputs, **kwargs)
            return result.get("output", "")
        except Exception as e:
            logger.error(f"Agent chat error: {e}")
            raise

    def chat_sync(
        self,
        message: str,
        chat_history: Optional[List[BaseMessage]] = None,
        **kwargs,
    ) -> str:
        """
        同步对话

        Args:
            message: 用户消息
            chat_history: 对话历史
            **kwargs: 其他参数

        Returns:
            Agent 响应
        """
        from datetime import datetime

        inputs = {
            "input": message,
            "current_date": datetime.now().strftime("%Y-%m-%d"),
        }

        if chat_history:
            inputs["chat_history"] = chat_history

        try:
            result = self.agent_executor.invoke(inputs, **kwargs)
            return result.get("output", "")
        except Exception as e:
            logger.error(f"Agent chat error: {e}")
            raise

    async def chat_stream(
        self,
        message: str,
        chat_history: Optional[List[BaseMessage]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        流式对话

        Args:
            message: 用户消息
            chat_history: 对话历史
            **kwargs: 其他参数

        Yields:
            Agent 响应片段
        """
        from datetime import datetime

        inputs = {
            "input": message,
            "current_date": datetime.now().strftime("%Y-%m-%d"),
        }

        if chat_history:
            inputs["chat_history"] = chat_history

        try:
            async for event in self.agent_executor.astream_events(
                inputs,
                version="v1",
                **kwargs,
            ):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield content
        except Exception as e:
            logger.error(f"Agent stream error: {e}")
            raise

    def add_tools(self, tools: List[BaseTool]) -> None:
        """添加工具"""
        self.tools.extend(tools)
        self._agent_executor = None  # 重置 executor

    def set_memory(self, memory: ConversationMemory) -> None:
        """设置记忆"""
        self.memory = memory
        self._agent_executor = None  # 重置 executor


# Agent 实例缓存
_agent_cache: Dict[str, WizyelabAgent] = {}


def create_agent(
    session_id: str = "default",
    tools: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
    **kwargs,
) -> WizyelabAgent:
    """
    创建 Agent 实例

    Args:
        session_id: 会话 ID
        tools: 工具名称列表
        system_prompt: 系统提示
        **kwargs: 其他参数

    Returns:
        WizyelabAgent 实例
    """
    # 获取工具
    if tools:
        agent_tools = get_tools_by_names(tools)
    else:
        agent_tools = get_default_tools()

    # 获取记忆
    memory = get_memory(session_id)

    # 创建 Agent
    agent = WizyelabAgent(
        tools=agent_tools,
        memory=memory,
        system_prompt=system_prompt,
        **kwargs,
    )

    # 缓存 Agent
    _agent_cache[session_id] = agent

    return agent


def get_agent(
    session_id: str = "default",
    create_if_not_exists: bool = True,
    **kwargs,
) -> Optional[WizyelabAgent]:
    """
    获取 Agent 实例

    Args:
        session_id: 会话 ID
        create_if_not_exists: 如果不存在是否创建
        **kwargs: 创建参数

    Returns:
        WizyelabAgent 实例
    """
    if session_id in _agent_cache:
        return _agent_cache[session_id]

    if create_if_not_exists:
        return create_agent(session_id, **kwargs)

    return None


def delete_agent(session_id: str) -> bool:
    """
    删除 Agent 实例

    Args:
        session_id: 会话 ID

    Returns:
        是否删除成功
    """
    if session_id in _agent_cache:
        del _agent_cache[session_id]
        logger.info(f"Agent deleted: {session_id}")
        return True
    return False
