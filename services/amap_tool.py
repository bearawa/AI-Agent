# -*- coding: utf-8 -*-
"""
AIZS 高德地图 API 工具集
封装天气查询、周边 POI 搜索、路线规划等功能。
所有工具均通过高德 Web 服务 API 获取真实数据。
"""
import time
import requests
from typing import Dict, Any, Optional
from config import settings
from utils.logger import logger
from mapping.location_mapper import location_mapper

# 相对日期偏移映射
_DATE_OFFSET = {"今天": 0, "今日": 0, "明天": 1, "明日": 1, "后天": 2}


def _http_get(url: str, params: dict, timeout: int = 8) -> dict:
    """统一 HTTP GET 请求封装，供测试 Mock。"""
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _resolve_adcode(city: str) -> str:
    """城市名解析为高德 adcode。未知城市返回原文让高德模糊匹配。"""
    return location_mapper.resolve_adcode(city)


def _is_today_query(date_str: str) -> bool:
    """判断日期描述是否指向今天（需实时天气而非预报）。"""
    normalized = date_str.strip().lower()
    return normalized in ["今天", "今日", "now"]


def get_weather_amap(city: str, date: str) -> Dict[str, Any]:
    """
    通过高德天气 API 查询指定城市和日期的天气信息。
    今天 → 实时天气；未来日期 → 天气预报。

    :param city: 城市名称，如 "南京"
    :param date: 日期描述，如 "今天"、"明天"、"2026-07-10"
    :return: 天气信息字典
    """
    api_key = settings.AMAP_API_KEY
    if not api_key:
        return {
            "city": city, "date": date,
            "error": "AMAP_API_KEY 未配置，无法查询天气",
            "is_demo": True, "notice": "高德 API Key 未配置"
        }

    adcode = _resolve_adcode(city)
    is_today = _is_today_query(date)
    extensions = "base" if is_today else "all"

    try:
        data = _http_get(
            f"{settings.AMAP_BASE_URL}/v3/weather/weatherInfo",
            params={"key": api_key, "city": adcode, "extensions": extensions, "output": "JSON"},
            timeout=8
        )

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            logger.error(f"高德天气 API 错误: {error_info}")
            return {"city": city, "date": date, "error": f"高德 API 错误: {error_info}", "is_demo": False}

        # 实时天气
        if is_today and "lives" in data and data["lives"]:
            live = data["lives"][0]
            return {
                "city": live.get("city", city),
                "date": "今天",
                "weather_status": live.get("weather", "未知"),
                "temperature": f"{live.get('temperature', '?')}°C",
                "wind_direction": live.get("winddirection", "无"),
                "wind_power": f"{live.get('windpower', '?')} 级",
                "humidity": f"{live.get('humidity', '?')}%",
                "report_time": live.get("reporttime", ""),
                "is_demo": False,
                "source": "高德天气 API"
            }

        # 天气预报
        if "forecasts" in data and data["forecasts"]:
            forecast = data["forecasts"][0]
            casts = forecast.get("casts", [])
            offset = _DATE_OFFSET.get(date.strip(), 0)
            target_cast = casts[offset] if 0 <= offset < len(casts) else (casts[0] if casts else None)

            if target_cast:
                week_names = "一二三四五六日"
                week_idx = int(target_cast.get("week", "1")) - 1
                return {
                    "city": forecast.get("city", city),
                    "province": forecast.get("province", ""),
                    "date": target_cast.get("date", date),
                    "week": f"星期{week_names[week_idx]}" if 0 <= week_idx < 7 else "",
                    "weather_status": target_cast.get("dayweather", "未知"),
                    "night_weather": target_cast.get("nightweather", "未知"),
                    "temperature_range": f"{target_cast.get('nighttemp', '?')}°C ~ {target_cast.get('daytemp', '?')}°C",
                    "day_wind": f"{target_cast.get('daywind', '')}风 {target_cast.get('daypower', '?')}级",
                    "night_wind": f"{target_cast.get('nightwind', '')}风 {target_cast.get('nightpower', '?')}级",
                    "is_demo": False,
                    "source": "高德天气 API"
                }

        return {"city": city, "date": date, "error": "高德天气 API 未返回有效数据", "is_demo": False}

    except requests.exceptions.Timeout:
        logger.error("高德天气 API 请求超时")
        return {"city": city, "date": date, "error": "高德天气 API 请求超时，请稍后重试", "is_demo": True, "notice": "网络超时"}
    except Exception as e:
        logger.error(f"高德天气 API 调用异常: {e}")
        return {"city": city, "date": date, "error": f"天气查询失败: {str(e)}", "is_demo": True, "notice": "调用异常"}


def search_nearby_poi(keyword: str, radius: int = 2000, city: str = "武汉") -> Dict[str, Any]:
    """
    搜索学校附近的兴趣点 (POI)。

    :param keyword: 搜索关键词，如 "医院"、"银行"
    :param radius: 搜索半径（米），默认 2000
    :param city: 城市名，默认 "南京"
    :return: POI 搜索结果字典
    """
    api_key = settings.AMAP_API_KEY
    if not api_key:
        return {
            "keyword": keyword, "error": "AMAP_API_KEY 未配置，无法执行 POI 搜索",
            "count": 0, "pois": [], "is_demo": True, "notice": "高德 API Key 未配置"
        }

    location = settings.AMAP_SCHOOL_LOCATION

    try:
        data = _http_get(
            f"{settings.AMAP_BASE_URL}/v5/place/around",
            params={
                "key": api_key, "location": location,
                "keywords": keyword, "radius": radius,
                "city": city, "output": "JSON",
                "page_size": 10, "extensions": "all"
            },
            timeout=8
        )

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            logger.error(f"高德 POI API 错误: {error_info}")
            return {"keyword": keyword, "error": f"高德 API 错误: {error_info}", "count": 0, "pois": [], "is_demo": False}

        pois_raw = data.get("pois", [])
        pois = []
        for p in pois_raw:
            pois.append({
                "name": p.get("name", ""),
                "type": p.get("type", ""),
                "address": p.get("address", "无详细地址"),
                "distance": p.get("distance", ""),
                "tel": p.get("tel", ""),
                "location": p.get("location", ""),
            })

        return {
            "keyword": keyword, "search_center": location, "radius": radius,
            "count": len(pois), "pois": pois,
            "is_demo": False, "source": "高德 POI API"
        }

    except requests.exceptions.Timeout:
        logger.error("高德 POI API 请求超时")
        return {"keyword": keyword, "error": "高德 POI API 请求超时", "count": 0, "pois": [], "is_demo": True, "notice": "网络超时"}
    except Exception as e:
        logger.error(f"高德 POI API 调用异常: {e}")
        return {"keyword": keyword, "error": f"POI 搜索失败: {str(e)}", "count": 0, "pois": [], "is_demo": True, "notice": "调用异常"}


def _geocode(address: str, city: str = "武汉") -> Optional[str]:
    """将地址文本转换为高德经纬度坐标 (经度,纬度)。失败返回 None。"""
    api_key = settings.AMAP_API_KEY
    if not api_key:
        return None
    try:
        data = _http_get(
            f"{settings.AMAP_BASE_URL}/v3/geocode/geo",
            params={"key": api_key, "address": address, "city": city, "output": "JSON"},
            timeout=5
        )
        if data.get("status") == "1" and data.get("geocodes"):
            return data["geocodes"][0].get("location")
        return None
    except Exception as e:
        logger.error(f"高德地理编码异常 ({address}): {e}")
        return None


def plan_route(origin: str, destination: str, mode: str = "walking") -> Dict[str, Any]:
    """
    规划从起点到终点的步行或骑行路线。

    :param origin: 起点名称或坐标
    :param destination: 终点名称或坐标
    :param mode: "walking"(步行) 或 "bicycling"(骑行)
    :return: 路线规划结果字典
    """
    api_key = settings.AMAP_API_KEY
    if not api_key:
        return {
            "origin": origin, "destination": destination,
            "error": "AMAP_API_KEY 未配置，无法执行路线规划",
            "is_demo": True, "notice": "高德 API Key 未配置"
        }

    # 坐标判定：含逗号视为已有坐标，否则先查校园地点映射，再地理编码
    if "," in origin:
        origin_coords = origin
    else:
        origin_coords = location_mapper.get_coords(origin) or _geocode(origin)
    
    if "," in destination:
        dest_coords = destination
    else:
        dest_coords = location_mapper.get_coords(destination) or _geocode(destination)

    if not origin_coords:
        return {"origin": origin, "destination": destination, "error": f"无法识别起点地址: {origin}", "is_demo": False}
    if not dest_coords:
        return {"origin": origin, "destination": destination, "error": f"无法识别终点地址: {destination}", "is_demo": False}

    api_path = "/v3/direction/walking" if mode == "walking" else "/v3/direction/bicycling"

    try:
        data = _http_get(
            f"{settings.AMAP_BASE_URL}{api_path}",
            params={"key": api_key, "origin": origin_coords, "destination": dest_coords, "output": "JSON"},
            timeout=8
        )

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            logger.error(f"高德路线规划 API 错误: {error_info}")
            return {"origin": origin, "destination": destination, "error": f"高德 API 错误: {error_info}", "is_demo": False}

        route = data.get("route", {})
        paths = route.get("paths", [])
        if not paths:
            return {"origin": origin, "destination": destination, "error": "未找到可用路线", "is_demo": False}

        path = paths[0]
        steps_raw = path.get("steps", [])
        steps = [{"instruction": s.get("instruction", ""), "road": s.get("road", ""), "distance": s.get("distance", ""), "duration": s.get("duration", "")} for s in steps_raw]

        distance_m = int(path.get("distance", "0"))
        duration_s = int(path.get("duration", "0"))
        distance_text = f"{distance_m} 米" if distance_m < 1000 else f"{distance_m / 1000:.1f} 公里"
        duration_text = f"{duration_s // 60} 分钟" if duration_s >= 60 else f"{duration_s} 秒"

        return {
            "origin": origin, "origin_coords": origin_coords,
            "destination": destination, "destination_coords": dest_coords,
            "mode": mode,
            "distance": str(distance_m), "distance_text": distance_text,
            "duration": str(duration_s), "duration_text": duration_text,
            "steps_count": len(steps), "steps": steps,
            "is_demo": False, "source": "高德路线规划 API"
        }

    except requests.exceptions.Timeout:
        logger.error("高德路线规划 API 请求超时")
        return {"origin": origin, "destination": destination, "error": "路线规划 API 请求超时", "is_demo": True, "notice": "网络超时"}
    except Exception as e:
        logger.error(f"高德路线规划 API 调用异常: {e}")
        return {"origin": origin, "destination": destination, "error": f"路线规划失败: {str(e)}", "is_demo": True, "notice": "调用异常"}
