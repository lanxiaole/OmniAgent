import sys
import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

# 确保项目根目录在 sys.path 中，这样无论从哪个目录启动都能找到 backend / agent_core 包
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# 初始化本次会话的日志文件（必须在 get_logger 之前调用）
from agent_core.logger import init_session_logger
init_session_logger()

from backend.routers.chat import router
from backend.routers import knowledge
from backend.routers import memory
from backend.routers import workspace
from backend.routers import models as models_router
from backend.routers import settings
from backend.routers import approval
from backend.routers import context
from agent_core.rag import build_vector_store
from agent_core.logger import get_logger

# 创建 logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时构建向量库，关闭时执行清理"""
    # 启动逻辑
    logger.info("应用启动中...")
    logger.info("检查知识库状态...")
    build_vector_store()
    logger.info("应用启动完成")
    yield
    # 关闭逻辑（目前无需清理，预留位置）
    logger.info("应用关闭")


# 创建 FastAPI 应用实例
app = FastAPI(title="OmniAgent API", lifespan=lifespan)

# ── 全局异常处理器 ──────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """捕获所有未处理的异常，返回统一的错误响应"""
    logger.error(f"未处理的异常: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"},
    )

@app.exception_handler(ImportError)
async def import_error_handler(request: Request, exc: ImportError):
    """处理模块导入错误，返回更友好的错误信息"""
    logger.error(f"模块导入失败: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"模块导入失败: {str(exc)}"},
    )

# 配置 CORS 中间件，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 HTTP 头
)

# 挂载路由，前缀为 /api
app.include_router(router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(workspace.router, prefix="/api")
app.include_router(models_router.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(approval.router, prefix="/api")
app.include_router(context.router, prefix="/api")


@app.get("/api/health")
async def health():
    """健康检查端点"""
    return {"message": "OmniAgent API is running"}


@app.get("/api/version")
async def version():
    return {
        "version": "1.1.0",
        "frozen": getattr(sys, 'frozen', False),
        "frontend_dir": _FRONTEND_DIR,
        "frontend_exists": os.path.isdir(_FRONTEND_DIR),
    }

# ── 前端静态文件托管 ──────────────────────────────────
# 生产模式：backend.exe 在 resources/backend/，前端在 resources/frontend/
# 开发模式：前端由 Vite dev server 独立托管，此处不生效
if getattr(sys, 'frozen', False):
    _FRONTEND_DIR = os.path.join(os.path.dirname(sys.executable), '..', 'frontend')
else:
    _FRONTEND_DIR = os.path.join(_PROJECT_ROOT, 'frontend', 'dist')

_FRONTEND_DIR = os.path.abspath(_FRONTEND_DIR)
print(f"[backend] 静态文件目录: {_FRONTEND_DIR}")
print(f"[backend] 目录存在: {os.path.isdir(_FRONTEND_DIR)}")

if os.path.isdir(_FRONTEND_DIR):
    # 用路由直接服务（避开 Starlette mount("/") 对根路径的空字符串坑）
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        """
        托管前端静态文件 + SPA 路由回退。
        /api/* 路由已注册，优先级高于此 catchall。
        """
        # 空路径 → index.html
        target = full_path if full_path else "index.html"
        file_path = os.path.join(_FRONTEND_DIR, target)
        # 文件存在则直接返回（如 /assets/xxx.js、/favicon.ico）
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # 其他所有路径 → SPA 回退到 index.html
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    # 支持 python main.py 直接启动（开发用）
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
