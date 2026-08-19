# 路径与目录配置模块
#
# 职责：
#   1. 计算并初始化用户数据目录（USER_DATA_DIR）与所有子目录。
#   2. 兼容旧数据目录（项目根目录 .env / workspace）的一次性迁移。
#   3. 定义各类子目录常量。
#
# 本模块为所有其他配置模块的依赖底层，不依赖本项目其他配置模块。

import os
import shutil
from pathlib import Path
import appdirs
from dotenv import load_dotenv


# =============================================================================
# 用户数据目录（操作系统标准位置）
# Windows: %APPDATA%\OmniAgent
# macOS:   ~/Library/Application Support/OmniAgent
# Linux:   ~/.local/share/OmniAgent
# =============================================================================
USER_DATA_DIR = appdirs.user_data_dir("OmniAgent", appauthor="", roaming=True)
os.makedirs(USER_DATA_DIR, exist_ok=True)

# 旧数据目录（项目根目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD_ENV_PATH = os.path.join(BASE_DIR, ".env")
OLD_WORKSPACE_PATH = os.path.join(BASE_DIR, "workspace")
NEW_ENV_PATH = os.path.join(USER_DATA_DIR, ".env")
NEW_WORKSPACE_PATH = os.path.join(USER_DATA_DIR, "workspace")

# 兼容迁移：若旧数据存在且新目录下没有，则自动迁移一次
_should_migrate_env = os.path.isfile(OLD_ENV_PATH) and not os.path.isfile(NEW_ENV_PATH)
_should_migrate_workspace = os.path.isdir(OLD_WORKSPACE_PATH) and not os.path.isdir(NEW_WORKSPACE_PATH)

if _should_migrate_env or _should_migrate_workspace:
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    if _should_migrate_env:
        shutil.move(OLD_ENV_PATH, NEW_ENV_PATH)
    if _should_migrate_workspace:
        shutil.move(OLD_WORKSPACE_PATH, NEW_WORKSPACE_PATH)

# 从 USER_DATA_DIR/.env 加载配置
load_dotenv(dotenv_path=NEW_ENV_PATH, override=True)


# =============================================================================
# 目录配置
# =============================================================================

# 所有 AI 生成的数据统一存放在 USER_DATA_DIR/workspace/ 下，便于备份和迁移
WORKSPACE_DIR = os.path.join(USER_DATA_DIR, "workspace")

# 子目录定义（使用 os.path.join 确保跨平台兼容）
CHECKPOINT_DIR = os.path.join(WORKSPACE_DIR, "checkpoints")
VECTOR_STORE_DIR = os.path.join(WORKSPACE_DIR, "vector_stores")
KNOWLEDGE_DIR = os.path.join(WORKSPACE_DIR, "knowledge")
LOGS_DIR = os.path.join(WORKSPACE_DIR, "logs")
CACHE_DIR = os.path.join(WORKSPACE_DIR, "cache")
TEMP_DIR = os.path.join(WORKSPACE_DIR, "temp")
UPLOAD_DIR = os.path.join(WORKSPACE_DIR, "uploads")
MEMORY_DIR = os.path.join(WORKSPACE_DIR, "memory")
FULL_HISTORY_DIR = os.path.join(WORKSPACE_DIR, "full_history")

# 确保所有目录存在
for _dir in [WORKSPACE_DIR, CHECKPOINT_DIR, VECTOR_STORE_DIR, KNOWLEDGE_DIR,
             LOGS_DIR, CACHE_DIR, TEMP_DIR, UPLOAD_DIR, MEMORY_DIR, FULL_HISTORY_DIR]:
    os.makedirs(_dir, exist_ok=True)

# 兼容旧模块引用（但值已指向 workspace 下的新路径）
PERSIST_DIR = VECTOR_STORE_DIR  # 原为 BASE_DIR/chroma_db


__all__ = [
    "USER_DATA_DIR",
    "BASE_DIR",
    "OLD_ENV_PATH",
    "OLD_WORKSPACE_PATH",
    "NEW_ENV_PATH",
    "NEW_WORKSPACE_PATH",
    "WORKSPACE_DIR",
    "CHECKPOINT_DIR",
    "VECTOR_STORE_DIR",
    "KNOWLEDGE_DIR",
    "LOGS_DIR",
    "CACHE_DIR",
    "TEMP_DIR",
    "UPLOAD_DIR",
    "MEMORY_DIR",
    "FULL_HISTORY_DIR",
    "PERSIST_DIR",
]