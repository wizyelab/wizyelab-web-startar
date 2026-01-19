"""
Agent 工具模块

定义 Agent 可使用的工具
"""

from typing import Any, Optional, Type
from abc import ABC

from langchain_core.tools import BaseTool as LangChainBaseTool
from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from pydantic import BaseModel, Field

from app.core.logging import setup_logger

logger = setup_logger(__name__)


class BaseTool(LangChainBaseTool, ABC):
    """
    自定义工具基类

    所有自定义工具都应继承此类
    """
    name: str = "base_tool"
    description: str = "Base tool"

    def _log_run(self, tool_input: str):
        """记录工具运行日志"""
        logger.info(f"Running tool: {self.name}, input: {tool_input}")


class SearchInput(BaseModel):
    """搜索工具输入"""
    query: str = Field(description="搜索查询")


class SearchTool(BaseTool):
    """
    搜索工具

    用于搜索相关信息
    """
    name: str = "search"
    description: str = "搜索相关信息，输入搜索查询"
    args_schema: Type[BaseModel] = SearchInput

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """同步运行"""
        self._log_run(query)
        # TODO: 实现实际的搜索逻辑
        return f"搜索结果: {query}"

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """异步运行"""
        self._log_run(query)
        # TODO: 实现实际的异步搜索逻辑
        return f"搜索结果: {query}"


class CalculatorInput(BaseModel):
    """计算器工具输入"""
    expression: str = Field(description="数学表达式")


class CalculatorTool(BaseTool):
    """
    计算器工具

    用于计算数学表达式
    """
    name: str = "calculator"
    description: str = "计算数学表达式，输入数学表达式"
    args_schema: Type[BaseModel] = CalculatorInput

    def _run(
        self,
        expression: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """同步运行"""
        self._log_run(expression)
        try:
            # 安全地评估数学表达式
            result = eval(expression, {"__builtins__": {}}, {})
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {e}"

    async def _arun(
        self,
        expression: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """异步运行"""
        return self._run(expression, run_manager)


class ProductSearchInput(BaseModel):
    """产品搜索工具输入"""
    query: str = Field(description="产品搜索查询")
    category: Optional[str] = Field(default=None, description="产品类别")


class ProductSearchTool(BaseTool):
    """
    产品搜索工具

    用于搜索运动装备产品
    """
    name: str = "product_search"
    description: str = "搜索运动装备产品，如网球拍、球鞋等"
    args_schema: Type[BaseModel] = ProductSearchInput

    def _run(
        self,
        query: str,
        category: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """同步运行"""
        self._log_run(f"{query} (category: {category})")
        # TODO: 实现实际的产品搜索逻辑
        return f"产品搜索结果: {query}"

    async def _arun(
        self,
        query: str,
        category: Optional[str] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """异步运行"""
        return self._run(query, category, run_manager)


class VideoAnalysisInput(BaseModel):
    """视频分析工具输入"""
    video_url: str = Field(description="视频 URL")
    analysis_type: str = Field(default="pose", description="分析类型: pose, technique, comparison")


class VideoAnalysisTool(BaseTool):
    """
    视频分析工具

    用于分析运动视频
    """
    name: str = "video_analysis"
    description: str = "分析运动视频，提取动作姿态和技术要点"
    args_schema: Type[BaseModel] = VideoAnalysisInput

    def _run(
        self,
        video_url: str,
        analysis_type: str = "pose",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """同步运行"""
        self._log_run(f"{video_url} (type: {analysis_type})")
        # TODO: 实现实际的视频分析逻辑
        return f"视频分析结果: {video_url}"

    async def _arun(
        self,
        video_url: str,
        analysis_type: str = "pose",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """异步运行"""
        return self._run(video_url, analysis_type, run_manager)


# 默认工具列表
DEFAULT_TOOLS = [
    SearchTool(),
    CalculatorTool(),
    ProductSearchTool(),
    VideoAnalysisTool(),
]


def get_default_tools():
    """获取默认工具列表"""
    return DEFAULT_TOOLS


def get_tools_by_names(names: list[str]) -> list[BaseTool]:
    """
    根据名称获取工具

    Args:
        names: 工具名称列表

    Returns:
        工具列表
    """
    tool_map = {tool.name: tool for tool in DEFAULT_TOOLS}
    return [tool_map[name] for name in names if name in tool_map]
