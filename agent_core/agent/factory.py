# Agent 工厂模块
# 提供依赖注入和可配置的 Agent 创建能力

from typing import Dict, Any, Optional, List, Callable
from langchain.agents import create_agent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from agent_core.agent.checkpointer import get_checkpointer
from agent_core.agent.model_factory import get_llm_model
from agent_core.agent.config import SYSTEM_PROMPT
from agent_core.agent.middleware import get_middlewares
from agent_core.errors import AgentCreationError
from agent_core.logger import get_logger

logger = get_logger(__name__)


class AgentFactory:
    """Agent 工厂类

    支持依赖注入，允许在测试中 Mock 掉 tools、model、checkpointer 等。
    通过配置字典创建 Agent 实例，实现解耦和可测试性。
    """

    def __init__(
        self,
        model: Optional[BaseLanguageModel] = None,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        checkpointer: Optional[Any] = None,
        middleware: Optional[Any] = None,
    ):
        """初始化工厂，接受可选的依赖注入

        Args:
            model: 语言模型实例（如果不提供，使用默认配置）
            tools: 工具列表（如果不提供，使用默认 TOOLS）
            system_prompt: 系统提示词（如果不提供，使用默认 SYSTEM_PROMPT）
            checkpointer: 检查点保存器（如果不提供，使用默认配置）
            middleware: 中间件实例（如果不提供，使用默认配置）
        """
        self.model = model
        self.tools = tools
        self.system_prompt = system_prompt
        self.checkpointer = checkpointer
        self.middleware = middleware

    def create_agent(self) -> Any:
        """创建 Agent 实例

        根据注入的依赖或默认配置创建 Agent。

        Returns:
            Any: Agent 执行器实例

        Raises:
            AgentCreationError: Agent 创建失败时抛出
        """
        try:
            logger.info("开始创建 Agent...")

            # 1. 获取或使用注入的依赖
            model = self.model or get_llm_model()
            tools = self.tools or self._get_default_tools()
            system_prompt = self.system_prompt or SYSTEM_PROMPT
            checkpointer = self.checkpointer or get_checkpointer()
            middleware = self.middleware or get_middlewares()

            # 2. 打印工具列表用于调试
            tool_names = [tool.name for tool in tools]
            logger.debug(f"可用工具列表: {tool_names}")

            # 3. 创建 Agent
            agent = create_agent(
                model=model,
                tools=tools,
                system_prompt=system_prompt,
                checkpointer=checkpointer,
                middleware=middleware,
            )

            logger.info("Agent 创建成功")
            return agent

        except Exception as e:
            logger.error(f"创建 Agent 失败: {e}", exc_info=True)
            raise AgentCreationError(f"创建 Agent 失败: {e}") from e

    def _get_default_tools(self) -> List[BaseTool]:
        """获取默认工具列表

        Returns:
            List[BaseTool]: 工具列表
        """
        from agent_core.tools import TOOLS
        return TOOLS

    def _get_default_checkpointer(self):
        """获取默认 checkpointer

        Returns:
            checkpointer 实例
        """
        return get_checkpointer()

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "AgentFactory":
        """从配置字典创建工厂实例

        Args:
            config: 配置字典，支持以下键：
                - model: 语言模型实例
                - tools: 工具列表
                - system_prompt: 系统提示词
                - checkpointer: 检查点保存器
                - middleware: 中间件实例

        Returns:
            AgentFactory: 工厂实例
        """
        return cls(
            model=config.get("model"),
            tools=config.get("tools"),
            system_prompt=config.get("system_prompt"),
            checkpointer=config.get("checkpointer"),
            middleware=config.get("middleware"),
        )


def create_agent_with_config(config: Optional[Dict[str, Any]] = None) -> Any:
    """使用配置创建 Agent（便捷函数）

    Args:
        config: 可选的配置字典

    Returns:
        Any: Agent 执行器实例
    """
    factory = AgentFactory.from_config(config or {})
    return factory.create_agent()


__all__ = [
    "AgentFactory",
    "create_agent_with_config",
]