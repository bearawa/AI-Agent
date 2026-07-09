import random
from typing import Dict, Any

def get_weather(city: str, date: str) -> Dict[str, Any]:
    """
    查询特定城市和日期的天气信息。
    重要：返回数据中必须明确标注“演示天气数据”。
    
    :param city: 城市名称，如 "南京", "北京"
    :param date: 查询日期，如 "今天", "明天", "2026-07-09"
    :return: 包含天气信息的字典
    """
    # 模拟几种常见的天气状况
    weathers = [
        {"status": "晴朗", "temp": "22°C ~ 30°C", "wind": "东风 3 级", "uv": "强"},
        {"status": "多云", "temp": "20°C ~ 28°C", "wind": "东南风 2 级", "uv": "中等"},
        {"status": "小雨", "temp": "18°C ~ 24°C", "wind": "北风 4 级", "uv": "弱"},
        {"status": "阴天", "temp": "19°C ~ 26°C", "wind": "微风 1 级", "uv": "极弱"}
    ]
    
    # 根据输入做一些伪随机或映射，使结果稳定但多样
    idx = (len(city) + len(date)) % len(weathers)
    weather_info = weathers[idx]
    
    return {
        "city": city,
        "date": date,
        "weather_status": weather_info["status"],
        "temperature_range": weather_info["temp"],
        "wind_direction_level": weather_info["wind"],
        "uv_index": weather_info["uv"],
        "is_demo": True,
        "notice": "演示天气数据，仅用于项目功能展示"
    }
