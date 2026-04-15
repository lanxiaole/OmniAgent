# OmniAgent 日志模块

import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger(name: str) -> logging.Logger:
    """获取 logger 实例
    
    参数:
        name: logger 名称，通常使用 __name__
        
    返回:
        logging.Logger: 配置好的 logger 实例
    """
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
    
    # 确保 logs 目录存在
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 文件 handler - DEBUG 级别，按大小滚动
    log_file = os.path.join(logs_dir, "omniagent.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding="utf-8"  # 使用 UTF-8 编码
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
