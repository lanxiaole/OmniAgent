# 场景系统数据层模块
#
# 职责：管理内置场景（只读）、用户自定义场景（可读写）与显示偏好。
#
# 存储结构：
#   内置场景：agent_core/config/scenarios.json（随程序分发，完全只读）
#   自定义场景：{USER_DATA_DIR}/scenarios/custom.json
#   显示偏好：{USER_DATA_DIR}/scenarios/display.json
#
# 本模块依赖 paths 模块提供的 USER_DATA_DIR。

import os
import json
import logging
from agent_core.config.paths import USER_DATA_DIR

# 场景配置文件路径（与 paths.py 同目录）—— 内置场景，随程序分发，完全只读
SCENARIOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios.json")

# 用户自定义场景与显示偏好的存储目录（用户数据目录内）
SCENARIOS_DIR = os.path.join(USER_DATA_DIR, "scenarios")
CUSTOM_SCENARIOS_FILE = os.path.join(SCENARIOS_DIR, "custom.json")
DISPLAY_FILE = os.path.join(SCENARIOS_DIR, "display.json")

# 自定义场景 ID 前缀，避免与内置场景 ID 冲突
_CUSTOM_ID_PREFIX = "custom_"

# 硬编码的默认预设（兜底方案）
_DEFAULT_PRESETS = [
    {
        "id": "default",
        "name": "通用助手",
        "icon": "ChatRound",
        "description": "均衡的日常助理，适用大部分场景",
        "system_prompt": "你是一个智能AI助手，名为 OmniAgent。",
        "enabled_tools": ["all"],
    }
]


def _create_default_scenarios_file() -> None:
    """创建默认的 scenarios.json 配置文件"""
    import shutil
    default_content = {
        "presets": [
            {
                "id": "default",
                "name": "通用助手",
                "icon": "ChatRound",
                "description": "均衡的日常助理，适用大部分场景",
                "system_prompt": "你是一个智能AI助手，名为 OmniAgent。\n\n## 核心能力\n你拥有以下工具可供使用，根据用户需求选择最合适的工具：\n\n### 信息查询\n- 当前时间查询\n- 联网搜索（获取实时信息）\n- 网页内容读取\n- 知识库检索（搜索本地知识库）\n\n### 天气查询\n- 查询指定城市天气\n\n### 记忆管理\n- 保存用户记忆（记住用户偏好和重要信息）\n- 回忆用户记忆（检索用户之前保存的信息）\n- 列出所有记忆\n- 删除指定记忆\n- 清空所有记忆\n\n### 文件操作\n- 读取文件内容\n- 写入文件（需要用户审批）\n- 列出目录内容\n- 搜索文件\n\n### 代码执行\n- 执行 Python 代码（需要用户审批）\n\n## 行为准则\n1. 始终使用中文回复用户，除非用户明确要求使用其他语言。\n2. 回答问题前，先充分理解用户意图。\n3. 使用工具时，清晰说明正在做什么以及为什么。\n4. 如果工具调用失败，给出友好的错误提示和替代方案。\n5. 对于需要审批的操作（写入文件、执行代码），先向用户说明将要执行的操作，等待用户确认。\n6. 联网搜索时，在回答中标注信息来源。\n7. 使用记忆功能记住用户的关键偏好和上下文信息，提供更个性化的服务。\n8. 如果你不知道答案或无法获取信息，诚实地告诉用户，不要编造信息。",
                "enabled_tools": ["all"],
            },
            {
                "id": "coder",
                "name": "编程专家",
                "icon": "Cpu",
                "description": "专注代码编写、调试与架构设计",
                "system_prompt": "你是一位资深软件工程师，精通多种编程语言和软件架构设计。\n\n## 核心能力\n你可以使用以下工具来协助编程任务：\n\n### 文件操作\n- 读取文件内容\n- 写入文件（需要用户审批）\n- 列出目录内容\n- 搜索文件\n\n### 代码执行\n- 执行 Python 代码（需要用户审批）\n\n### 信息查询\n- 联网搜索（查找技术文档、解决方案）\n- 网页内容读取\n- 当前时间查询\n\n### 记忆管理\n- 保存用户记忆\n- 回忆用户记忆\n\n## 行为准则\n1. 始终使用中文回复用户，除非用户明确要求使用其他语言。\n2. 在编写代码前，先理解需求并给出设计方案。\n3. 注释使用中文，代码中的变量名、函数名使用英文。\n4. 注重代码质量：可读性、可维护性、性能和安全性。\n5. 对于需要审批的操作，先向用户说明将要执行的操作。\n6. 调试时，系统性地分析问题，给出根因分析和修复方案。\n7. 提供完整的代码示例，而不仅仅是代码片段。\n8. 如果用户的项目涉及框架，遵循该框架的最佳实践和约定。",
                "enabled_tools": ["read_file", "write_file", "list_directory", "search_files", "execute_python", "search_web", "read_webpage", "get_current_time", "save_user_memory", "recall_user_memory"],
            },
            {
                "id": "researcher",
                "name": "研究顾问",
                "icon": "Search",
                "description": "深度信息检索与分析，研究报告撰写",
                "system_prompt": "你是一位专业的研究顾问，擅长信息检索、数据分析和研究报告撰写。\n\n## 核心能力\n你可以使用以下工具来进行研究工作：\n\n### 信息查询\n- 联网搜索（多角度搜索，获取全面信息）\n- 网页内容读取（深入阅读源材料）\n- 知识库检索（查询本地知识库）\n\n### 记忆管理\n- 保存用户记忆（保存研究过程中的关键发现）\n- 回忆用户记忆\n- 列出所有记忆\n- 删除指定记忆\n- 清空所有记忆\n\n### 文件操作\n- 读取文件内容\n- 写入文件（保存研究笔记和报告，需要用户审批）\n- 列出目录内容\n- 搜索文件\n\n### 代码执行\n- 执行 Python 代码（数据分析、数据可视化，需要用户审批）\n\n## 行为准则\n1. 始终使用中文回复用户，除非用户明确要求使用其他语言。\n2. 研究过程要系统化：先明确问题，再收集信息，然后分析，最后得出结论。\n3. 多源交叉验证，避免单一信息源的偏见。\n4. 在回答中标注信息来源，提供可追溯的引用链接。\n5. 对于复杂主题，提供结构化的分析报告。\n6. 区分事实和观点，对不确定的信息说明置信度。\n7. 如果信息不足，明确指出局限性并建议进一步的研究方向。\n8. 保存关键研究发现到记忆中，以便后续查询时参考。",
                "enabled_tools": ["search_web", "read_webpage", "search_knowledge", "get_current_time", "save_user_memory", "recall_user_memory", "list_user_memories", "delete_user_memory", "clear_user_memories", "read_file", "write_file", "list_directory", "search_files", "execute_python"],
            },
            {
                "id": "writer",
                "name": "创意写作",
                "icon": "EditPen",
                "description": "文章创作、文案润色与内容策划",
                "system_prompt": "你是一位专业的创意写作助手，擅长各类文体创作、文案润色和内容策划。\n\n## 核心能力\n你可以使用以下工具辅助写作工作：\n\n### 信息查询\n- 联网搜索（查找参考资料和素材）\n- 网页内容读取\n- 当前时间查询\n\n### 记忆管理\n- 保存用户记忆（记住写作风格偏好）\n- 回忆用户记忆\n\n### 文件操作\n- 读取文件内容\n- 写入文件（保存创作内容，需要用户审批）\n- 列出目录内容\n- 搜索文件\n\n## 行为准则\n1. 始终使用中文回复用户，除非用户明确要求使用其他语言。\n2. 创作前先了解目标受众、文体要求和风格偏好。\n3. 提供多种写作方案供用户选择。\n4. 注重文字的美感、节奏和表现力。\n5. 润色时保留原文的核心信息和风格，提升表达质量。\n6. 对于长篇内容，提供清晰的结构大纲。\n7. 引用的资料和数据标注来源。\n8. 保存用户的写作风格偏好到记忆中，以便持续提供一致的写作体验。",
                "enabled_tools": ["search_web", "read_webpage", "get_current_time", "save_user_memory", "recall_user_memory", "read_file", "write_file", "list_directory", "search_files"],
            },
        ]
    }
    try:
        os.makedirs(os.path.dirname(SCENARIOS_FILE), exist_ok=True)
        with open(SCENARIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_content, f, ensure_ascii=False, indent=2)
        logging.getLogger(__name__).info(f"[Scenario] 已创建默认场景配置文件: {SCENARIOS_FILE}")
    except Exception as e:
        logging.getLogger(__name__).warning(f"[Scenario] 创建默认场景配置文件失败: {e}")


def load_scenarios() -> dict:
    """读取 scenarios.json 并解析为 Python 字典

    如果文件不存在，自动创建默认配置文件后返回。
    如果文件存在但解析失败，记录错误日志并返回硬编码兜底配置。

    Returns:
        dict: 包含 presets 列表的字典
    """
    logger = logging.getLogger(__name__)

    # 文件不存在，自动创建
    if not os.path.isfile(SCENARIOS_FILE):
        logger.info(f"[Scenario] 场景配置文件不存在，自动创建: {SCENARIOS_FILE}")
        _create_default_scenarios_file()

    # 读取并解析
    try:
        with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "presets" not in data or not isinstance(data["presets"], list):
            raise ValueError("scenarios.json 缺少 presets 字段或不是数组")
        return data
    except Exception as e:
        logger.error(f"[Scenario] 加载配置文件失败，使用默认配置: {e}")
        return {"presets": _DEFAULT_PRESETS}


def get_scenario(scenario_id: str) -> dict:
    """获取指定 ID 的场景预设

    同时在内置场景与用户自定义场景中查找。
    如果找不到匹配的场景，回退到 default 预设。
    返回值始终包含所有必填字段。

    Args:
        scenario_id: 场景唯一标识符

    Returns:
        dict: 场景配置对象
    """
    logger = logging.getLogger(__name__)
    scenarios = get_all_scenarios()

    # 查找匹配的场景
    for scenario in scenarios:
        if scenario.get("id") == scenario_id:
            return scenario

    # 查找 default 预设
    for scenario in scenarios:
        if scenario.get("id") == "default":
            logger.warning(
                f"[Scenario] 未找到场景 '{scenario_id}'，回退到 default"
            )
            return scenario

    # 连 default 都没有，返回硬编码兜底
    logger.warning(
        f"[Scenario] 未找到场景 '{scenario_id}' 且无 default 预设，使用硬编码兜底"
    )
    return dict(_DEFAULT_PRESETS[0])


def get_current_scenario_id() -> str:
    """从 .env 文件读取 OMNI_SCENARIO 环境变量

    实时读取（不使用缓存），因为用户可能在运行时切换场景。
    如果未设置，返回 "default"。

    Returns:
        str: 当前场景 ID
    """
    return os.getenv("OMNI_SCENARIO", "default")


def get_active_system_prompt() -> str:
    """获取当前场景的 System Prompt

    此函数完全替代原有的 SYSTEM_PROMPT 常量。
    所有调用方都应迁移到此函数。

    Returns:
        str: 当前场景的 system_prompt 文本
    """
    scenario_id = get_current_scenario_id()
    scenario = get_scenario(scenario_id)
    return scenario.get("system_prompt", "")


def _load_scenarios_file(path: str) -> list[dict]:
    """读取场景文件，返回场景列表；文件不存在或解析失败时返回空列表"""
    if not os.path.isfile(path) or not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        scenarios = data.get("scenarios", [])
        return scenarios if isinstance(scenarios, list) else []
    except Exception:
        logging.getLogger(__name__).warning(f"[Scenario] 读取场景文件失败: {path}")
        return []


def _save_scenarios_file(path: str, scenarios: list[dict]) -> None:
    """将场景列表写入文件（原子写入，避免写坏文件）"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"scenarios": scenarios}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_builtin_scenarios() -> list[dict]:
    """加载内置场景（只读）

    返回内置于程序目录的场景列表，统一附加 is_system=True 标识。

    Returns:
        list[dict]: 内置场景列表
    """
    presets = [dict(p) for p in load_scenarios().get("presets", [])]
    for p in presets:
        p["is_system"] = True
    return presets


def load_custom_scenarios() -> list[dict]:
    """加载用户自定义场景，统一附加 is_system=False 标识

    Returns:
        list[dict]: 自定义场景列表
    """
    scenarios = _load_scenarios_file(CUSTOM_SCENARIOS_FILE)
    for s in scenarios:
        s["is_system"] = False
    return scenarios


def save_custom_scenarios(scenarios: list[dict]) -> None:
    """保存用户自定义场景列表

    持久化时剔除 is_system / display 等运行时附加字段。

    Args:
        scenarios: 自定义场景列表
    """
    cleaned = []
    for s in scenarios:
        cleaned.append({
            "id": s.get("id"),
            "name": s.get("name", ""),
            "icon": s.get("icon", "ChatRound"),
            "description": s.get("description", ""),
            "system_prompt": s.get("system_prompt", ""),
            "enabled_tools": s.get("enabled_tools", ["all"]),
        })
    _save_scenarios_file(CUSTOM_SCENARIOS_FILE, cleaned)


def load_display_prefs() -> dict:
    """加载显示偏好，返回 {scenario_id: bool}

    未配置的场景默认视为显示（True）。

    Returns:
        dict: 显示偏好映射
    """
    if not os.path.isfile(DISPLAY_FILE):
        return {}
    try:
        with open(DISPLAY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        prefs = data.get("display", {}) if isinstance(data, dict) else {}
        return prefs if isinstance(prefs, dict) else {}
    except Exception:
        logging.getLogger(__name__).warning(f"[Scenario] 读取显示偏好失败: {DISPLAY_FILE}")
        return {}


def save_display_prefs(prefs: dict) -> None:
    """保存显示偏好（原子写入）"""
    os.makedirs(os.path.dirname(DISPLAY_FILE), exist_ok=True)
    tmp = f"{DISPLAY_FILE}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"display": prefs}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DISPLAY_FILE)


def get_all_scenarios() -> list[dict]:
    """合并内置场景与自定义场景，内置在前

    每个场景额外附加 is_system 与 display 字段，供前端展示与过滤。

    Returns:
        list[dict]: 全量场景列表
    """
    builtin = load_builtin_scenarios()
    custom = load_custom_scenarios()
    display = load_display_prefs()
    for s in builtin + custom:
        s["display"] = display.get(s["id"], True)
    return builtin + custom


def _generate_scenario_id() -> str:
    """生成与内置/现有自定义场景均不冲突的场景 ID"""
    import uuid
    existing = {s["id"] for s in (load_builtin_scenarios() + load_custom_scenarios())}
    while True:
        sid = f"{_CUSTOM_ID_PREFIX}{uuid.uuid4().hex[:8]}"
        if sid not in existing:
            return sid


def create_custom_scenario(data: dict) -> dict:
    """创建自定义场景并持久化，返回创建后的场景字典

    Args:
        data: 包含 name / icon / description / system_prompt / enabled_tools

    Returns:
        dict: 创建后的场景（含 id 与运行时标识）
    """
    scenarios = load_custom_scenarios()
    scenario = {
        "id": _generate_scenario_id(),
        "name": str(data.get("name", "")).strip() or "未命名场景",
        "icon": data.get("icon", "ChatRound"),
        "description": data.get("description", ""),
        "system_prompt": data.get("system_prompt", ""),
        "enabled_tools": data.get("enabled_tools", ["all"]),
        "is_system": False,
        "display": True,
    }
    scenarios.append({k: v for k, v in scenario.items() if k not in ("is_system", "display")})
    save_custom_scenarios(scenarios)
    return scenario


def delete_custom_scenario(scenario_id: str) -> str:
    """删除自定义场景

    Returns:
        str: 'ok' 删除成功；'builtin' 系统内置不可删除；'not_found' 不存在
    """
    if scenario_id in {s["id"] for s in load_builtin_scenarios()}:
        return "builtin"
    scenarios = load_custom_scenarios()
    remaining = [s for s in scenarios if s["id"] != scenario_id]
    if len(remaining) == len(scenarios):
        return "not_found"
    save_custom_scenarios(remaining)
    return "ok"


def duplicate_custom_scenario(scenario_id: str) -> dict | None:
    """复制自定义场景，返回新场景；目标不存在或为内置时返回 None

    Args:
        scenario_id: 源自定义场景 ID

    Returns:
        dict | None: 新场景字典，失败返回 None
    """
    scenarios = load_custom_scenarios()
    source = next((s for s in scenarios if s["id"] == scenario_id), None)
    if source is None:
        return None
    new_scenario = {
        "id": _generate_scenario_id(),
        "name": f"{source.get('name', '未命名场景')} (副本)",
        "icon": source.get("icon", "ChatRound"),
        "description": source.get("description", ""),
        "system_prompt": source.get("system_prompt", ""),
        "enabled_tools": source.get("enabled_tools", ["all"]),
        "is_system": False,
        "display": True,
    }
    scenarios.append({k: v for k, v in new_scenario.items() if k not in ("is_system", "display")})
    save_custom_scenarios(scenarios)
    return new_scenario


def update_custom_scenario(scenario_id: str, data: dict) -> dict | None:
    """更新自定义场景内容（内置场景只读，不可编辑）

    Args:
        scenario_id: 场景 ID
        data: 新的场景字段

    Returns:
        dict | None: 更新后的场景；目标不存在或为内置场景返回 None
    """
    if scenario_id in {s["id"] for s in load_builtin_scenarios()}:
        return None
    scenarios = load_custom_scenarios()
    idx = next((i for i, s in enumerate(scenarios) if s["id"] == scenario_id), None)
    if idx is None:
        return None
    scenario = scenarios[idx]
    scenario["name"] = str(data.get("name", scenario.get("name", ""))).strip() or "未命名场景"
    scenario["icon"] = data.get("icon", scenario.get("icon", "ChatRound"))
    scenario["description"] = data.get("description", scenario.get("description", ""))
    scenario["system_prompt"] = data.get("system_prompt", scenario.get("system_prompt", ""))
    scenario["enabled_tools"] = data.get("enabled_tools", scenario.get("enabled_tools", ["all"]))
    save_custom_scenarios(scenarios)
    return {**scenario, "is_system": False, "display": load_display_prefs().get(scenario_id, True)}


def update_scenario_display(scenario_id: str, display: bool) -> None:
    """更新场景的显示偏好（内置与自定义均支持）"""
    prefs = load_display_prefs()
    prefs[scenario_id] = display
    save_display_prefs(prefs)


def import_custom_scenario(data: dict) -> dict:
    """导入场景并持久化，作为自定义场景

    导入的场景 ID 若与内置场景或现有自定义场景冲突，会自动重新生成，保证不冲突。

    Args:
        data: 导入的场景数据字典

    Returns:
        dict: 导入后的自定义场景
    """
    builtin_ids = {s["id"] for s in load_builtin_scenarios()}
    custom_ids = {s["id"] for s in load_custom_scenarios()}
    source_id = str(data.get("id", "")).strip()
    if source_id and source_id not in builtin_ids and source_id not in custom_ids:
        sid = source_id
    else:
        sid = _generate_scenario_id()

    scenario = {
        "id": sid,
        "name": str(data.get("name", "")).strip() or "未命名场景",
        "icon": data.get("icon", "ChatRound"),
        "description": data.get("description", ""),
        "system_prompt": data.get("system_prompt", ""),
        "enabled_tools": data.get("enabled_tools", ["all"]),
    }
    scenarios = load_custom_scenarios()
    scenarios.append(scenario)
    save_custom_scenarios(scenarios)
    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "icon": scenario["icon"],
        "description": scenario["description"],
        "system_prompt": scenario["system_prompt"],
        "enabled_tools": scenario["enabled_tools"],
        "is_system": False,
        "display": True,
    }


def export_scenario_data(scenario_id: str) -> dict | None:
    """导出场景原始数据（不含运行时附加字段）

    Args:
        scenario_id: 场景 ID（内置/自定义均可）

    Returns:
        dict | None: 场景原始数据，未找到返回 None
    """
    match = next((s for s in get_all_scenarios() if s["id"] == scenario_id), None)
    if match is None:
        return None
    return {
        "id": match["id"],
        "name": match["name"],
        "icon": match["icon"],
        "description": match["description"],
        "system_prompt": match["system_prompt"],
        "enabled_tools": match["enabled_tools"],
    }


__all__ = [
    "SCENARIOS_FILE",
    "SCENARIOS_DIR",
    "CUSTOM_SCENARIOS_FILE",
    "DISPLAY_FILE",
    "load_scenarios",
    "get_scenario",
    "get_current_scenario_id",
    "get_active_system_prompt",
    "load_builtin_scenarios",
    "load_custom_scenarios",
    "save_custom_scenarios",
    "load_display_prefs",
    "save_display_prefs",
    "get_all_scenarios",
    "create_custom_scenario",
    "delete_custom_scenario",
    "duplicate_custom_scenario",
    "update_custom_scenario",
    "update_scenario_display",
    "import_custom_scenario",
    "export_scenario_data",
]