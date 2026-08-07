# OmniAgent 日志模块

import logging
import os
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

from agent_core.config.settings import LOGS_DIR
# 日志保留天数
LOG_RETENTION_DAYS = 7

# 本次启动的日志文件名（带时间戳和PID，避免多进程冲突）
_session_log_file = None
_fallback_to_console = False  # 日志写入失败时的回退标志


def _ensure_logs_dir():
    """确保日志目录存在"""
    try:
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
    except PermissionError:
        print(f"[Logger] 无法创建日志目录（权限不足）: {LOGS_DIR}")
        raise


def _cleanup_old_logs():
    """清理过期日志文件"""
    cutoff_time = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    cleaned_count = 0
    
    if not os.path.exists(LOGS_DIR):
        return 0
    
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith(".log"):
            try:
                # 文件名格式: omniagent_20260728_084043_pid12345.log
                # 提取时间戳部分（跳过_pid后缀）
                name_without_ext = filename.replace(".log", "")
                # 查找 _pid 分隔点
                pid_idx = name_without_ext.find("_pid")
                if pid_idx > 0:
                    date_str = name_without_ext[:pid_idx]
                else:
                    date_str = name_without_ext
                
                file_time = datetime.strptime(date_str.replace("omniagent_", ""), "%Y%m%d_%H%M%S")
                if file_time < cutoff_time:
                    try:
                        os.remove(os.path.join(LOGS_DIR, filename))
                        cleaned_count += 1
                    except PermissionError:
                        # 文件被占用，跳过
                        pass
            except ValueError:
                pass
            except PermissionError:
                pass
    
    return cleaned_count


def init_session_logger():
    """初始化本次会话的日志文件（在应用启动时调用一次）
    
    Returns:
        str: 本次会话的日志文件路径
    """
    global _session_log_file, _fallback_to_console
    
    # 如果已经初始化过，直接返回
    if _session_log_file is not None:
        return _session_log_file
    
    try:
        _ensure_logs_dir()
    except PermissionError:
        _fallback_to_console = True
        _session_log_file = "CONSOLE_ONLY"
        print("[Logger] 将仅使用控制台输出，不写入日志文件")
        return _session_log_file
    
    # 生成带时间戳和PID的日志文件名，避免多进程冲突
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pid = os.getpid()
    _session_log_file = os.path.join(LOGS_DIR, f"omniagent_{timestamp}_pid{pid}.log")
    
    # 清理过期日志
    try:
        cleaned_count = _cleanup_old_logs()
        if cleaned_count > 0:
            print(f"[Cleanup] Removed {cleaned_count} old log file(s)")
    except Exception as e:
        print(f"[Cleanup] 清理旧日志时出错: {e}")
    
    print(f"[Session] Log file: {_session_log_file}")
    
    return _session_log_file


def get_logger(name: str) -> logging.Logger:
    """获取 logger 实例
    
    参数:
        name: logger 名称，通常使用 __name__
        
    返回:
        logging.Logger: 配置好的 logger 实例
    """
    global _session_log_file, _fallback_to_console
    
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
    
    # 如果回退到控制台模式，直接返回
    if _fallback_to_console:
        return logger
    
    # 确保日志目录存在
    try:
        _ensure_logs_dir()
    except PermissionError:
        _fallback_to_console = True
        print("[Logger] 将仅使用控制台输出，不写入日志文件")
        return logger
    
    # 如果还没有初始化会话日志，先生成一个
    if _session_log_file is None:
        init_session_logger()
    
    # 如果是控制台-only模式，直接返回
    if _session_log_file == "CONSOLE_ONLY":
        return logger
    
    # 文件 handler - 写入本次会话的日志文件
    try:
        file_handler = RotatingFileHandler(
            _session_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, IOError) as e:
        # 文件写入失败，回退到控制台模式
        print(f"[Logger] 无法创建日志文件，回退到控制台模式: {e}")
        _fallback_to_console = True
        # 移除控制台handler外的其他handler
        logger.handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    
    return logger
