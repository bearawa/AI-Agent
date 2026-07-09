# -*- coding: utf-8 -*-
"""
展示格式化工具集 —— AIZS 统一的空值保护与格式化函数。
所有页面应使用本模块中的函数替代空值参与数值运算等不安全操作。
"""
import json
from typing import Any, Optional


def safe_text(value: Any, default: str = "暂无") -> str:
    """
    安全地将值转换为文本，空值返回默认提示。
    """
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def format_percent(value: Any, default: str = "暂无") -> str:
    """
    将 0.0~1.0 的浮点数格式化为百分比字符串，如 '85.0%'。
    空值或异常返回默认提示。
    """
    if value is None:
        return default
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return default


def format_confidence(value: Any, default: str = "暂无") -> str:
    """
    将置信度（0.0~1.0）格式化为百分比字符串，如 '95.0%'。
    专用于意图置信度展示。
    """
    return format_percent(value, default)


def format_ms(value: Any, default: str = "暂无") -> str:
    """
    将毫秒值格式化为带单位的字符串，如 '123 ms'。
    空值返回默认提示。
    """
    if value is None:
        return default
    try:
        return f"{int(value)} ms"
    except (TypeError, ValueError):
        return default


def format_score(value: Any, total: int = 5, default: str = "暂无") -> str:
    """
    将评分格式化为 'X / 5' 形式，空值返回默认提示。
    """
    if value is None:
        return default
    try:
        return f"{int(value)} / {total}"
    except (TypeError, ValueError):
        return default


def format_bool_status(value: Any, true_text: str = "是", false_text: str = "否", default: str = "暂无") -> str:
    """
    将布尔值或 0/1 格式化为中文状态文本。
    """
    if value is None:
        return default
    try:
        return true_text if bool(int(value)) else false_text
    except (TypeError, ValueError):
        return default


def truncate_text(text: Any, max_length: int = 80) -> str:
    """
    截断文本到指定长度，超出部分用省略号代替。
    """
    if text is None:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def safe_json_preview(value: Any, max_length: int = 120) -> str:
    """
    安全地预览 JSON 字符串或字典/列表，空值返回空字符串。
    """
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            text = json.dumps(value, ensure_ascii=False, indent=None)
        except (TypeError, ValueError):
            text = str(value)
    else:
        text = str(value)
    return truncate_text(text, max_length)
