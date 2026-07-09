import logging
import os
import sys
from config import settings

def setup_logger(name="campus_service"):
    """
    配置并获取全局 logger。
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # 设置日志级别
    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    logger.setLevel(log_level)

    # 日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 终端输出处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出处理器，显式指定编码为 utf-8 以支持中文
    try:
        file_handler = logging.FileHandler(settings.LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"初始化日志文件处理器失败: {e}", file=sys.stderr)

    return logger

# 暴露出默认的全局 logger
logger = setup_logger()
