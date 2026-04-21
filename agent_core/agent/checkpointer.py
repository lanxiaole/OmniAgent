# Checkpointer 配置模块
import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver
from agent_core.logger import get_logger

logger = get_logger(__name__)


def get_checkpointer():
    """创建并返回 SqliteSaver 实例
    
    Returns:
        SqliteSaver: 检查点保存实例
    """
    # 数据库文件路径（存放在 agent_core/data/ 下）
    DATA_DIR = Path(__file__).parent.parent / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "agent_checkpoints.db"
    
    # 创建 SQLite 连接
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    
    # 创建 SqliteSaver 实例
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()
    
    logger.info(f"Checkpointer 已初始化，数据库路径: {DB_PATH}")
    
    return checkpointer
