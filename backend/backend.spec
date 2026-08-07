# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 - OmniAgent 后端
=====================================
打包 backend/main.py（FastAPI + uvicorn）为单个 exe 文件。

使用方法：
    cd .. && .venv\Scripts\python -m PyInstaller backend\backend.spec --clean --distpath backend\dist

输出位置：backend/dist/backend.exe
"""

import sys
from pathlib import Path

# ── 项目路径 ──────────────────────────────────────────
# SPECPATH：PyInstaller exec() 执行时提供的 spec 文件目录（替代 __file__）
SPEC_DIR = Path(SPECPATH).resolve()
# 项目根目录
PROJECT_ROOT = SPEC_DIR.parent

# ── 数据文件 ──────────────────────────────────────────
# 需要打包到 exe 旁边的静态资源
DATAS = [
    # Agent 系统提示词
    (str(PROJECT_ROOT / "agent_core" / "prompts" / "system.txt"),
     "agent_core/prompts"),
    # 城市编码数据
    (str(PROJECT_ROOT / "agent_core" / "resources" / "AMap_adcode_citycode.xlsx"),
     "agent_core/resources"),
    (str(PROJECT_ROOT / "agent_core" / "resources" / "city_codes.json"),
     "agent_core/resources"),
]

# ── 隐式导入 ──────────────────────────────────────────
# PyInstaller 无法自动检测动态导入的模块，需要手动列出
HIDDEN_IMPORTS = [
    # ── FastAPI 路由 ──
    "backend.routers.chat",
    "backend.routers.knowledge",
    "backend.routers.memory",
    "backend.routers.workspace",
    "backend.routers.models",
    "backend.routers.settings",
    "backend.routers.approval",
    "backend.schemas.chat",
    "backend.schemas.knowledge",
    "backend.schemas.memory",
    "backend.schemas.models",
    "backend.schemas.settings",
    "backend.schemas.workspace",
    "backend.services.agent_service",

    # ── Agent Core 模块 ──
    "agent_core.agent",
    "agent_core.agent.checkpointer",
    "agent_core.agent.config",
    "agent_core.agent.executor",
    "agent_core.agent.factory",
    "agent_core.agent.middleware",
    "agent_core.agent.model_factory",
    "agent_core.config",
    "agent_core.config.prompt_loader",
    "agent_core.config.settings",
    "agent_core.executor",
    "agent_core.executor.python_executor",
    "agent_core.logger",
    "agent_core.logger.setup",
    "agent_core.memory",
    "agent_core.memory.memory_manager",
    "agent_core.rag",
    "agent_core.rag.builder",
    "agent_core.rag.config",
    "agent_core.rag.loaders",
    "agent_core.rag.retriever",
    "agent_core.search",
    "agent_core.search.cache",
    "agent_core.search.tavily_engine",
    "agent_core.tools",
    "agent_core.tools.executor_tool",
    "agent_core.tools.file_tool",
    "agent_core.tools.memory_tool",
    "agent_core.tools.rag_tool",
    "agent_core.tools.search_tool",
    "agent_core.tools.time_tool",
    "agent_core.tools.weather_tool",

    # ── LangChain / LangGraph 相关 ──
    "langchain_community",
    "langchain_openai",
    "langchain_core",
    "langchain_core.tools",
    "langchain_chroma",
    "langgraph",
    "langgraph.checkpoint",
    "langgraph.checkpoint.sqlite",
    "langgraph_checkpoint_sqlite",

    # ── ChromaDB 相关 ──
    "chromadb",
    "chromadb.api.segment",
    "chromadb.api.fastapi",

    # ── 其他依赖 ──
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.middleware",
    "uvicorn.middleware.wsgi",
    "fastapi",
    "pydantic",
    "pydantic_settings",
    "dotenv",
    "appdirs",
    "tavily",
    "requests",
    "dateutil",
    "dateutil.parser",
    "multipart",
    "yaml",
    "sqlite3",
    "json",
    "csv",
    "hashlib",
]

# ── 排除不需要的模块（减小体积） ──────────────────────
EXCLUDES = [
    "tkinter",
    "matplotlib",
    "scipy",
    "sympy",
    "PIL",
    "pillow",
    "cv2",
    "numpy.testing",
    "pandas",
    "notebook",
    "jupyter",
    "ipython",
]

# ── 入口脚本 ──────────────────────────────────────────
# 创建一个临时入口脚本，用于启动 uvicorn 服务器
# 这样可以避免直接打包 backend/main.py 导致路径问题
ENTRY_SCRIPT = str(SPEC_DIR / "_run_backend.py")

# 生成入口脚本
_RUN_SCRIPT_CONTENT = '''"""
OmniAgent 后端启动入口（PyInstaller 打包用）
"""
import sys
import os

# 确保 exe 所在目录在 sys.path 中
_EXE_DIR = os.path.dirname(os.path.abspath(__file__))
if _EXE_DIR not in sys.path:
    sys.path.insert(0, _EXE_DIR)

# 项目根目录（exe 的父目录）
_PROJECT_ROOT = os.path.dirname(_EXE_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# 初始化日志
from agent_core.logger import init_session_logger
init_session_logger()

# 启动 FastAPI 服务器
import uvicorn
from backend.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
'''

# 写入入口脚本
_run_script_path = Path(ENTRY_SCRIPT)
_run_script_path.write_text(_RUN_SCRIPT_CONTENT, encoding="utf-8")

# ── PyInstaller 配置 ──────────────────────────────────
a = Analysis(
    [ENTRY_SCRIPT],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=DATAS,
    hiddenimports=HIDDEN_IMPORTS,
    excludes=EXCLUDES,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="backend",               # 输出 exe 文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                 # 保留控制台窗口，方便调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                    # 可替换为 resources/icons/ 中的图标
)

# 打包完成后清理临时入口脚本
import atexit

def _cleanup():
    _p = Path(ENTRY_SCRIPT)
    if _p.exists():
        _p.unlink()

atexit.register(_cleanup)