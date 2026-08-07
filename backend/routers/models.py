# 模型管理路由
# 提供模型配置的 CRUD 操作，配置存储在 .env 文件中

import os
import re
from fastapi import APIRouter, HTTPException
from backend.schemas.models import (
    ModelAddRequest,
    ModelUpdateRequest,
    ModelConfigResponse,
    ModelListResponse,
    ModelTestRequest,
)
from agent_core.config.settings import read_env, write_env_key, delete_env_key
from agent_core.logger import get_logger

# langchain_openai 延迟导入，避免打包后缺失时影响整个应用启动
try:
    from langchain_openai import ChatOpenAI
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False
    logger = get_logger(__name__)
    logger.warning("langchain_openai 不可用，模型测试功能将受限")

logger = get_logger(__name__)

router = APIRouter()

# ==================== 常量 ====================
MODEL_PREFIX = "OMNI_MODEL_"

# LLM 运行时环境变量名（模型工厂依赖这些变量）
LLM_BASE_URL_KEY = "LLM_BASE_URL"
LLM_API_KEY_KEY = "LLM_API_KEY"
LLM_MODEL_KEY = "LLM_MODEL"


# ==================== 核心工具函数 ====================

def generate_model_id(name: str) -> str:
    """根据名称生成 ID：小写 + 下划线，去除特殊字符"""
    # 去除特殊字符，替换空格为下划线
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    return re.sub(r'\s+', '_', clean.lower())


def parse_model_config(env_vars: dict, model_id: str) -> dict:
    """从环境变量字典中解析单个模型配置"""
    prefix = f"{MODEL_PREFIX}{model_id}_"
    return {
        "id": model_id,
        "name": env_vars.get(f"{prefix}NAME", ""),
        "provider": env_vars.get(f"{prefix}PROVIDER", ""),
        "base_url": env_vars.get(f"{prefix}BASE_URL", ""),
        "api_key": env_vars.get(f"{prefix}API_KEY", ""),
        "model": env_vars.get(f"{prefix}MODEL", ""),
        "is_default": env_vars.get(f"{prefix}DEFAULT", "0") == "1",
    }


def mask_api_key(key: str) -> str:
    """对 API Key 进行脱敏：前4位 + **** + 后4位"""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "****" + key[-4:]


def get_all_models() -> list[dict]:
    """获取所有已配置的模型"""
    env_vars = read_env()
    model_ids = set()
    for key in env_vars.keys():
        if key.startswith(MODEL_PREFIX) and key.endswith("_NAME"):
            model_id = key[len(MODEL_PREFIX):-len("_NAME")]
            model_ids.add(model_id)
    return [parse_model_config(env_vars, mid) for mid in model_ids]


def save_model_config(model_id: str, config: dict) -> None:
    """保存模型配置到 .env"""
    prefix = f"{MODEL_PREFIX}{model_id}_"
    write_env_key(f"{prefix}NAME", config["name"])
    write_env_key(f"{prefix}PROVIDER", config["provider"])
    write_env_key(f"{prefix}BASE_URL", config["base_url"])
    write_env_key(f"{prefix}API_KEY", config["api_key"])
    write_env_key(f"{prefix}MODEL", config["model"])
    if config.get("is_default"):
        # 将其他模型的 DEFAULT 置 0
        for existing in get_all_models():
            if existing["id"] != model_id and existing["is_default"]:
                write_env_key(f"{MODEL_PREFIX}{existing['id']}_DEFAULT", "0")
        write_env_key(f"{prefix}DEFAULT", "1")
        # 同步到 LLM 运行时环境变量，确保模型工厂能读到正确的配置
        sync_default_model_to_llm_env()
        # 重置全局 Agent，下次调用时使用新模型
        reset_global_agent()
    else:
        write_env_key(f"{prefix}DEFAULT", "0")


def delete_model_config(model_id: str) -> bool:
    """删除模型的所有配置项"""
    prefix = f"{MODEL_PREFIX}{model_id}_"
    env_vars = read_env()
    keys_to_delete = [k for k in env_vars.keys() if k.startswith(prefix)]
    if not keys_to_delete:
        return False
    for key in keys_to_delete:
        delete_env_key(key)
    return True


def to_response(model: dict) -> ModelConfigResponse:
    """将模型配置字典转换为响应对象（脱敏 API Key）"""
    return ModelConfigResponse(
        id=model["id"],
        name=model["name"],
        provider=model["provider"],
        base_url=model["base_url"],
        api_key_masked=mask_api_key(model["api_key"]),
        model=model["model"],
        is_default=model["is_default"],
    )


def get_current_model_id() -> str | None:
    """获取当前默认模型的 ID"""
    for model in get_all_models():
        if model["is_default"]:
            return model["id"]
    return None


def sync_default_model_to_llm_env() -> None:
    """将当前默认模型的配置同步到 LLM_* 环境变量

    模型工厂 (model_factory.py) 依赖 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
    三个环境变量创建 LLM 实例。当用户通过设置页面切换默认模型时，
    必须将默认模型的配置同步到这三个变量，确保模型工厂能读到正确的配置。
    """
    default_model = None
    for model in get_all_models():
        if model["is_default"]:
            default_model = model
            break

    if default_model:
        write_env_key(LLM_BASE_URL_KEY, default_model["base_url"])
        write_env_key(LLM_API_KEY_KEY, default_model["api_key"])
        write_env_key(LLM_MODEL_KEY, default_model["model"])
        logger.info(
            f"默认模型已同步到 LLM 运行时环境: "
            f"{default_model['name']} ({default_model['model']})"
        )
    else:
        # 没有默认模型时，清除 LLM_* 变量避免使用过期配置
        for key in [LLM_BASE_URL_KEY, LLM_API_KEY_KEY, LLM_MODEL_KEY]:
            if key in os.environ:
                delete_env_key(key)
        logger.info("没有默认模型，已清除 LLM 运行时环境变量")


def reset_global_agent() -> None:
    """重置全局 Agent 执行器，使下次调用时重新创建（热更新模型）

    在 sync_default_model_to_llm_env() 之后调用，确保新创建的 Agent
    使用最新的模型配置。
    """
    try:
        from agent_core.agent.executor import _global_agent_executor as ga
        if ga is not None:
            # 将全局 Agent 置为 None，下次 _get_global_agent() 会重新创建
            import agent_core.agent.executor as executor_module
            executor_module._global_agent_executor = None
            logger.info("全局 Agent 执行器已重置，下次调用将重新创建")
    except ImportError:
        logger.warning("无法导入 executor 模块，跳过 Agent 重置")


# ==================== API 端点 ====================

@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """获取所有模型列表"""
    models = get_all_models()
    current_id = get_current_model_id()
    return ModelListResponse(
        models=[to_response(m) for m in models],
        current_id=current_id,
    )


@router.post("/models", response_model=ModelConfigResponse)
async def add_model(request: ModelAddRequest):
    """添加新模型"""
    # 如果名称为空，则使用模型名作为显示名称
    name = request.name.strip() if request.name else request.model
    if not name:
        raise HTTPException(status_code=400, detail="模型名称和模型名不能同时为空")

    # 检查是否存在同名模型
    existing = get_all_models()
    for m in existing:
        if m["name"] == name:
            raise HTTPException(status_code=400, detail=f"已存在同名模型: {name}")

    model_id = generate_model_id(name)

    # 如果已有模型，检查是否与已有 ID 冲突
    for m in existing:
        if m["id"] == model_id and m["name"] != request.name:
            # ID 冲突但名称不同，添加后缀
            import random
            model_id = f"{model_id}_{random.randint(100, 999)}"

    # 如果还没有任何模型，自动设为默认
    is_default = len(existing) == 0

    config = {
        "name": name,
        "provider": request.provider,
        "base_url": request.base_url,
        "api_key": request.api_key,
        "model": request.model,
        "is_default": is_default,
    }
    save_model_config(model_id, config)

    config["id"] = model_id
    logger.info(f"模型添加成功: {model_id} ({name})")
    return to_response(config)


@router.put("/models/{model_id}", response_model=ModelConfigResponse)
async def update_model(model_id: str, request: ModelUpdateRequest):
    """更新模型配置"""
    models = get_all_models()
    target = None
    for m in models:
        if m["id"] == model_id:
            target = m
            break

    if target is None:
        raise HTTPException(status_code=404, detail=f"模型不存在: {model_id}")

    # 检查名称是否与其他模型冲突
    if request.name is not None and request.name != target["name"]:
        for m in models:
            if m["id"] != model_id and m["name"] == request.name:
                raise HTTPException(status_code=400, detail=f"已存在同名模型: {request.name}")

    # 更新字段（只更新提供的字段）
    update_data = {}
    for field in ["name", "provider", "base_url", "api_key", "model"]:
        value = getattr(request, field, None)
        if value is not None:
            update_data[field] = value

    merged = {**target, **update_data}
    merged["is_default"] = target["is_default"]
    save_model_config(model_id, merged)

    merged["id"] = model_id
    logger.info(f"模型更新成功: {model_id}")
    return to_response(merged)


@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """删除模型配置"""
    # 检查模型是否存在
    models = get_all_models()
    target = None
    for m in models:
        if m["id"] == model_id:
            target = m
            break

    if target is None:
        raise HTTPException(status_code=404, detail=f"模型不存在: {model_id}")

    success = delete_model_config(model_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除模型配置失败")

    # 如果删除的是默认模型，将默认切换到第一个可用模型
    if target["is_default"]:
        remaining = get_all_models()
        if remaining:
            first = remaining[0]
            first["is_default"] = True
            save_model_config(first["id"], first)
            logger.info(f"默认模型已切换到: {first['id']}")

    logger.info(f"模型删除成功: {model_id}")
    return {"success": True, "message": f"模型已删除: {model_id}"}


@router.post("/models/{model_id}/default")
async def set_default_model(model_id: str):
    """将指定模型设为默认"""
    models = get_all_models()
    target = None
    for m in models:
        if m["id"] == model_id:
            target = m
            break

    if target is None:
        raise HTTPException(status_code=404, detail=f"模型不存在: {model_id}")

    target["is_default"] = True
    save_model_config(model_id, target)

    logger.info(f"默认模型已设置为: {model_id}")
    return {"success": True, "message": f"默认模型已设置为: {target['name']}"}


@router.get("/models/current")
async def get_current_model():
    """获取当前正在使用的模型"""
    models = get_all_models()
    for m in models:
        if m["is_default"]:
            return to_response(m)
    # 没有默认模型，返回第一个
    if models:
        return to_response(models[0])
    raise HTTPException(status_code=404, detail="未配置任何模型")


@router.post("/models/test")
async def test_model_connection(request: ModelTestRequest):
    """测试模型连接是否有效"""
    if not _LANGCHAIN_AVAILABLE:
        return {"success": False, "error": "langchain_openai 模块不可用"}
    
    try:
        # 创建临时 LLM 实例发送测试消息
        llm = ChatOpenAI(
            model=request.model,
            base_url=request.base_url,
            api_key=request.api_key,
            temperature=0.0,
            timeout=15,  # 15 秒超时
        )
        result = llm.invoke("ping")
        # 检查是否正常响应
        if result and result.content:
            return {"success": True, "message": "连接成功"}
        else:
            return {"success": False, "error": "模型返回了空响应"}
    except Exception as e:
        logger.warning(f"模型测试连接失败: {e}")
        return {"success": False, "error": str(e)}