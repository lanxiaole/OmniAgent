# Agent 工厂模块
# 提供依赖注入和可配置的 Agent 创建能力

from typing import Dict, Any, Optional, List, Callable
from langchain.agents import create_agent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from agent_core.agent.checkpointer import get_checkpointer
from agent_core.agent.model_factory import get_llm_model
from agent_core.agent.middleware import get_middlewares
from agent_core.errors import AgentCreationError
from agent_core.logger import get_logger
from agent_core.config.settings import (
    get_current_scenario_id,
    get_scenario,
    get_active_system_prompt,
)

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
            system_prompt: 系统提示词（如果不提供，使用当前场景的 system_prompt）
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

        根据注入的依赖或当前场景配置创建 Agent。
        场景切换仅影响新创建的 Agent，不改变已有会话。

        Returns:
            Any: Agent 执行器实例

        Raises:
            AgentCreationError: Agent 创建失败时抛出
        """
        try:
            # 获取当前场景配置
            scenario_id = get_current_scenario_id()
            scenario = get_scenario(scenario_id)
            logger.info(f"[Scenario] 使用场景: {scenario_id} ({scenario.get('name', '')})")

            # 获取或使用注入的依赖
            model = self.model or get_llm_model()
            tools = self.tools or self._get_default_tools(scenario)
            system_prompt = self.system_prompt or get_active_system_prompt()
            checkpointer = self.checkpointer or get_checkpointer()
            middleware = self.middleware or get_middlewares()

            # 打印工具列表用于调试
            tool_names = [tool.name for tool in tools]
            logger.info(f"[Scenario] 启用 {len(tool_names)} 个工具: {tool_names}")

            # 创建 Agent
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

    def _get_default_tools(self, scenario: Optional[dict] = None) -> List[BaseTool]:
        """根据场景配置获取默认工具列表

        如果场景指定了 enabled_tools，则从 TOOLS 中过滤出匹配的工具。
        如果 enabled_tools 为 ["all"]，则使用完整的 TOOLS 列表。

        Args:
            scenario: 场景配置字典，包含 enabled_tools 字段

        Returns:
            List[BaseTool]: 过滤后的工具列表
        """
        from agent_core.tools import TOOLS

        if scenario is None:
            return TOOLS

        enabled_tools = scenario.get("enabled_tools", ["all"])

        # ["all"] 表示启用所有工具
        if enabled_tools == ["all"]:
            return TOOLS

        # 构建 {tool.name: tool} 映射以实现 O(1) 查找
        tool_map = {tool.name: tool for tool in TOOLS}

        filtered_tools = []
        for name in enabled_tools:
            if name in tool_map:
                filtered_tools.append(tool_map[name])
            else:
                logger.debug(f"[Scenario] 工具 '{name}' 在 TOOLS 列表中不存在，已忽略")

        return filtered_tools

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