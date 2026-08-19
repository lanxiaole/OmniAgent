"""
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
