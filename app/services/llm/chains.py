"""
LangChain Chains 模块

提供常用的 Chain 模板
"""

from typing import Optional, List, Dict, Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.chains import ConversationChain, LLMChain
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.services.llm.llm_client import get_chat_model
from app.services.llm.memory import ConversationMemory, get_memory
from app.core.logging import setup_logger

logger = setup_logger(__name__)


def create_conversation_chain(
    llm: Optional[BaseChatModel] = None,
    memory: Optional[ConversationMemory] = None,
    system_prompt: Optional[str] = None,
) -> ConversationChain:
    """
    创建对话 Chain

    Args:
        llm: LLM 实例
        memory: 记忆实例
        system_prompt: 系统提示

    Returns:
        对话 Chain
    """
    llm = llm or get_chat_model()
    memory = memory or get_memory()

    default_system_prompt = """你是 Wizyelab 智能助手，专注于运动装备推荐和运动技能提升。
你可以帮助用户:
1. 推荐合适的运动装备（如网球拍、球鞋等）
2. 分析运动视频，提供技术改进建议
3. 回答运动相关的问题

请用友好、专业的方式与用户交流。"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt or default_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])

    chain = ConversationChain(
        llm=llm,
        memory=memory.memory,
        prompt=prompt,
        verbose=settings.agent.verbose,
    )

    return chain


def create_qa_chain(
    llm: Optional[BaseChatModel] = None,
    system_prompt: Optional[str] = None,
) -> Any:
    """
    创建问答 Chain（无记忆）

    Args:
        llm: LLM 实例
        system_prompt: 系统提示

    Returns:
        问答 Chain
    """
    llm = llm or get_chat_model()

    default_system_prompt = """你是一个专业的运动顾问。
请根据用户的问题，提供准确、有帮助的回答。"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt or default_system_prompt),
        ("human", "{question}"),
    ])

    chain = prompt | llm | StrOutputParser()

    return chain


def create_rag_chain(
    llm: Optional[BaseChatModel] = None,
    retriever=None,
    system_prompt: Optional[str] = None,
) -> Any:
    """
    创建 RAG Chain

    Args:
        llm: LLM 实例
        retriever: 检索器
        system_prompt: 系统提示

    Returns:
        RAG Chain
    """
    llm = llm or get_chat_model()

    default_system_prompt = """你是一个专业的运动顾问。
请根据以下上下文信息回答用户的问题。

上下文信息:
{context}

如果上下文信息不足以回答问题，请说明你不确定，并提供你所知道的相关信息。"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt or default_system_prompt),
        ("human", "{question}"),
    ])

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    if retriever:
        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
    else:
        # 没有检索器时，直接使用空上下文
        chain = (
            {"context": lambda x: "", "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

    return chain


def create_structured_output_chain(
    llm: Optional[BaseChatModel] = None,
    output_schema: Any = None,
    system_prompt: Optional[str] = None,
) -> Any:
    """
    创建结构化输出 Chain

    Args:
        llm: LLM 实例
        output_schema: 输出 schema（Pydantic 模型）
        system_prompt: 系统提示

    Returns:
        结构化输出 Chain
    """
    llm = llm or get_chat_model()

    if output_schema:
        structured_llm = llm.with_structured_output(output_schema)
    else:
        structured_llm = llm

    default_system_prompt = """请根据用户的输入，返回结构化的信息。"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt or default_system_prompt),
        ("human", "{input}"),
    ])

    chain = prompt | structured_llm

    return chain


def create_product_recommendation_chain(
    llm: Optional[BaseChatModel] = None,
) -> Any:
    """
    创建产品推荐 Chain

    Args:
        llm: LLM 实例

    Returns:
        产品推荐 Chain
    """
    llm = llm or get_chat_model()

    system_prompt = """你是一个专业的运动装备顾问，专门帮助用户选择合适的运动装备。

在推荐时，请考虑以下因素:
1. 用户的运动水平（初学者/中级/高级）
2. 用户的预算
3. 用户的具体需求和偏好
4. 产品的性价比和口碑

请提供详细的推荐理由，包括产品的优缺点分析。

用户信息:
{user_profile}

用户问题: {question}"""

    prompt = ChatPromptTemplate.from_template(system_prompt)

    chain = prompt | llm | StrOutputParser()

    return chain
