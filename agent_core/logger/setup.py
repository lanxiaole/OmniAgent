# OmniAgent 日志模块

import logging
import os
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

# 日志目录（项目根目录下的 logs 文件夹）
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
# 日志保留天数
LOG_RETENTION_DAYS = 7

# 本次启动的日志文件名（带时间戳）
_session_log_file = None


def _ensure_logs_dir():
    """确保日志目录存在"""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)


def _cleanup_old_logs():
    """清理过期日志文件"""
    cutoff_time = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    cleaned_count = 0
    
    if not os.path.exists(LOGS_DIR):
        return 0
    
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith(".log"):
            try:
                # 文件名格式: omniagent_20260728_084043.log
                date_str = filename.replace("omniagent_", "").replace(".log", "")
                file_time = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                if file_time < cutoff_time:
                    os.remove(os.path.join(LOGS_DIR, filename))
                    cleaned_count += 1
            except ValueError:
                pass
    
    return cleaned_count


def init_session_logger():
    """初始化本次会话的日志文件（在应用启动时调用一次）
    
    Returns:
        str: 本次会话的日志文件路径
    """
    global _session_log_file
    
    # 如果已经初始化过，直接返回
    if _session_log_file is not None:
        return _session_log_file
    
    _ensure_logs_dir()
    
    # 生成带时间戳的日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _session_log_file = os.path.join(LOGS_DIR, f"omniagent_{timestamp}.log")
    
    # 清理过期日志
    cleaned_count = _cleanup_old_logs()
    
    if cleaned_count > 0:
        print(f"🗑️  已清理 {cleaned_count} 个过期日志文件")
    
    print(f"📝 本次会话日志: {_session_log_file}")
    
    return _session_log_file


def get_logger(name: str) -> logging.Logger:
    """获取 logger 实例
    
    参数:
        name: logger 名称，通常使用 __name__
        
    返回:
        logging.Logger: 配置好的 logger 实例
    """
    global _session_log_file
    
    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 如果 logger 已经有 handler，直接返回（避免重复配置）
    if logger.handlers:
        return logger
    
    # 定义日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 控制台 handler - INFO 级别
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 确保日志目录存在
    _ensure_logs_dir()
    
    # 如果还没有初始化会话日志，先生成一个
    if _session_log_file is None:
        init_session_logger()
    
    # 文件 handler - 写入本次会话的日志文件
    file_handler = RotatingFileHandler(
        _session_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
