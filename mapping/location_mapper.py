# -*- coding: utf-8 -*-
"""
AIZS 位置映射器
管理校园地点到坐标的转换，支持动态扩展。
"""
from typing import Dict, Any, List, Optional, Tuple
from mapping.framework import location_registry
from utils.logger import logger


class LocationMapper:
    """校园地点到坐标的映射器"""
    
    CAMPUS_LOCATIONS: Dict[str, Dict[str, str]] = {
        "教学楼": {"name": "文溯楼", "coords": "114.3926,30.4753"},
        "文溯楼": {"name": "文溯楼", "coords": "114.3926,30.4753"},
        "图书馆": {"name": "南湖图书馆", "coords": "114.3935,30.4762"},
        "南湖图书馆": {"name": "南湖图书馆", "coords": "114.3935,30.4762"},
        "食堂": {"name": "西苑食堂", "coords": "114.3918,30.4745"},
        "西苑食堂": {"name": "西苑食堂", "coords": "114.3918,30.4745"},
        "体育馆": {"name": "南湖体育馆", "coords": "114.3942,30.4770"},
        "南湖体育馆": {"name": "南湖体育馆", "coords": "114.3942,30.4770"},
        "宿舍": {"name": "西苑宿舍", "coords": "114.3915,30.4740"},
        "西苑宿舍": {"name": "西苑宿舍", "coords": "114.3915,30.4740"},
        "校门口": {"name": "学校南门", "coords": "114.3930,30.4730"},
        "南门": {"name": "学校南门", "coords": "114.3930,30.4730"},
        "北门": {"name": "学校北门", "coords": "114.3925,30.4780"},
        "行政楼": {"name": "行政楼", "coords": "114.3938,30.4758"},
        "实验楼": {"name": "实验楼", "coords": "114.3945,30.4765"},
        "操场": {"name": "南操场", "coords": "114.3948,30.4775"},
        "南操场": {"name": "南操场", "coords": "114.3948,30.4775"},
    }
    
    CITY_ADCODE_MAP: Dict[str, str] = {
        "南京": "320100",
        "北京": "110000",
        "上海": "310000",
        "广州": "440100",
        "深圳": "440300",
        "杭州": "330100",
        "成都": "510100",
        "武汉": "420100",
        "西安": "610100",
        "苏州": "320500",
        "无锡": "320200",
        "重庆": "500000",
        "天津": "120000",
        "长沙": "430100",
        "郑州": "410100",
        "合肥": "340100",
        "济南": "370100",
        "青岛": "370200",
        "大连": "210200",
        "厦门": "350200",
        "福州": "350100",
        "宁波": "330200",
        "南京财经": "320100",
        "中南财经": "420100",
    }
    
    def __init__(self):
        self._initialize_registry()
    
    def _initialize_registry(self):
        """初始化位置注册表"""
        for alias, info in self.CAMPUS_LOCATIONS.items():
            location_registry.register(
                key=alias,
                item=info,
                metadata={
                    "type": "campus",
                    "name": info["name"],
                    "coords": info["coords"]
                }
            )
        
        for city, adcode in self.CITY_ADCODE_MAP.items():
            location_registry.register(
                key=f"city_{city}",
                item=adcode,
                metadata={
                    "type": "city",
                    "city": city,
                    "adcode": adcode
                }
            )
        
        logger.info("位置映射器初始化完成")
    
    def get_coords(self, location_name: str) -> Optional[str]:
        """
        根据地点名称获取坐标
        
        :param location_name: 地点名称
        :return: 坐标字符串 "经度,纬度"，未找到返回 None
        """
        info = self.CAMPUS_LOCATIONS.get(location_name)
        if info:
            return info["coords"]
        return None
    
    def get_location_info(self, location_name: str) -> Optional[Dict[str, str]]:
        """
        获取地点的完整信息
        
        :param location_name: 地点名称
        :return: 包含 name 和 coords 的字典，未找到返回 None
        """
        return self.CAMPUS_LOCATIONS.get(location_name)
    
    def resolve_adcode(self, city: str) -> str:
        """
        解析城市名称为高德 adcode
        
        :param city: 城市名称
        :return: adcode，未找到返回原文
        """
        for name, code in self.CITY_ADCODE_MAP.items():
            if name in city:
                return code
        return city
    
    def get_city_name(self, adcode: str) -> Optional[str]:
        """
        根据 adcode 获取城市名称
        
        :param adcode: 城市编码
        :return: 城市名称，未找到返回 None
        """
        for city, code in self.CITY_ADCODE_MAP.items():
            if code == adcode:
                return city
        return None
    
    def is_campus_location(self, location_name: str) -> bool:
        """检查是否为校园地点"""
        return location_name in self.CAMPUS_LOCATIONS
    
    def is_city(self, city_name: str) -> bool:
        """检查是否为已知城市"""
        return city_name in self.CITY_ADCODE_MAP
    
    def add_campus_location(self, alias: str, name: str, coords: str):
        """
        添加新的校园地点
        
        :param alias: 地点别名
        :param name: 正式名称
        :param coords: 坐标 "经度,纬度"
        """
        self.CAMPUS_LOCATIONS[alias] = {"name": name, "coords": coords}
        location_registry.register(
            key=alias,
            item={"name": name, "coords": coords},
            metadata={"type": "campus", "name": name, "coords": coords}
        )
        logger.info(f"添加校园地点: {alias} -> {name} ({coords})")
    
    def add_city(self, city_name: str, adcode: str):
        """
        添加新的城市映射
        
        :param city_name: 城市名称
        :param adcode: 高德 adcode
        """
        self.CITY_ADCODE_MAP[city_name] = adcode
        location_registry.register(
            key=f"city_{city_name}",
            item=adcode,
            metadata={"type": "city", "city": city_name, "adcode": adcode}
        )
        logger.info(f"添加城市映射: {city_name} -> {adcode}")
    
    def list_campus_locations(self) -> List[Dict[str, Any]]:
        """获取所有校园地点"""
        result = []
        seen = set()
        for alias, info in self.CAMPUS_LOCATIONS.items():
            if info["name"] not in seen:
                seen.add(info["name"])
                result.append({
                    "name": info["name"],
                    "coords": info["coords"],
                    "aliases": [k for k, v in self.CAMPUS_LOCATIONS.items() if v["name"] == info["name"]]
                })
        return result
    
    def list_cities(self) -> List[Dict[str, Any]]:
        """获取所有城市映射"""
        result = []
        for city, adcode in self.CITY_ADCODE_MAP.items():
            result.append({"city": city, "adcode": adcode})
        return result


# 全局位置映射器实例
location_mapper = LocationMapper()
