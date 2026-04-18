import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.chat import router

# 确保能导入根目录的 agent 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

# 创建 FastAPI 应用实例
app = FastAPI()

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


@app.get("/")
async def root():
    """健康检查端点"""
    return {"message": "OmniAgent API is running"}
