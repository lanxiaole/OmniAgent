import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
async def root():
    """健康检查端点"""
    return {"message": "OmniAgent API is running"}


if __name__ == "__main__":
    # 支持 python main.py 直接启动（开发用）
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
