FROM python:3.11-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制依赖配置
COPY requirements.txt ./

# 直接用 pip 安装依赖（更简单，避免构建问题）
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY agent_core ./agent_core
COPY backend ./backend
COPY main.py .

# 创建必要的目录
RUN mkdir -p chroma_db logs agent_core/data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')" || exit 1

# 启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
