# Agent 配置模块

from agent_core.config.prompt_loader import load_prompt

# 系统提示：统一从 prompts/system.txt 读取，修改 prompt 只需编辑该文件
SYSTEM_PROMPT = load_prompt("system")
