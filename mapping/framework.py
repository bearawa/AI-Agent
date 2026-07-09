# -*- coding: utf-8 -*-
"""
AIZS 映射框架核心
提供统一的注册器和路由管理器，支持工具、意图、位置的注册和查找。
"""
from typing import Dict, Any, List, Optional, Callable
from utils.logger import logger


class Registry:
    """统一注册器，支持工具、意图、位置的注册和查找"""
    
    def __init__(self, name: str):
        self.name = name
        self._registry: Dict[str, Dict[str, Any]] = {}
    
    def register(self, key: str, item, metadata: Optional[Dict[str, Any]] = None):
        """
        注册一个项目到注册表
        
        :param key: 唯一标识
        :param item: 注册项（可以是函数、类、配置等）
        :param metadata: 元数据，包含描述、参数、返回值等信息
        """
        if key in self._registry:
            logger.warning(f"[{self.name}] 已存在注册项: {key}，将被覆盖")
        
        self._registry[key] = {
            "item": item,
            "metadata": metadata or {}
        }
        logger.info(f"[{self.name}] 注册成功: {key}")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取注册项
        
        :param key: 唯一标识
        :return: 包含 item 和 metadata 的字典，不存在返回 None
        """
        return self._registry.get(key)
    
    def get_item(self, key: str):
        """
        获取注册项的实际对象
        
        :param key: 唯一标识
        :return: 注册的对象，不存在返回 None
        """
        entry = self._registry.get(key)
        return entry["item"] if entry else None
    
    def get_metadata(self, key: str) -> Dict[str, Any]:
        """
        获取注册项的元数据
        
        :param key: 唯一标识
        :return: 元数据字典，不存在返回空字典
        """
        entry = self._registry.get(key)
        return entry["metadata"] if entry else {}
    
    def list_all(self) -> List[str]:
        """获取所有注册键"""
        return list(self._registry.keys())
    
    def list_with_metadata(self) -> List[Dict[str, Any]]:
        """获取所有注册项及其元数据"""
        result = []
        for key, entry in self._registry.items():
            result.append({
                "key": key,
                "item": entry["item"],
                **entry["metadata"]
            })
        return result
    
    def unregister(self, key: str) -> bool:
        """
        注销一个注册项
        
        :param key: 唯一标识
        :return: 是否成功注销
        """
        if key in self._registry:
            del self._registry[key]
            logger.info(f"[{self.name}] 注销成功: {key}")
            return True
        return False
    
    def clear(self):
        """清空注册表"""
        self._registry.clear()
        logger.info(f"[{self.name}] 注册表已清空")


class Router:
    """路由管理器，根据意图/上下文路由到对应服务"""
    
    def __init__(self):
        self._routes: Dict[str, Dict[str, Any]] = {}
    
    def add_route(self, intent: str, service_name: str, handler: Callable = None, **kwargs):
        """
        添加路由规则
        
        :param intent: 意图分类
        :param service_name: 目标服务名称
        :param handler: 处理函数
        :param kwargs: 额外参数
        """
        if intent in self._routes:
            logger.warning(f"路由意图 {intent} 已存在，将被覆盖")
        
        self._routes[intent] = {
            "service_name": service_name,
            "handler": handler,
            "params": kwargs
        }
        logger.info(f"添加路由: {intent} -> {service_name}")
    
    def route(self, intent: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        根据意图查找路由
        
        :param intent: 意图分类
        :param context: 上下文信息
        :return: 路由信息字典，不存在返回 None
        """
        route = self._routes.get(intent)
        if route:
            result = {**route}
            if context:
                result["context"] = context
            return result
        
        logger.warning(f"未找到意图 '{intent}' 的路由，回退到默认处理")
        return self._routes.get("default")
    
    def get_service_name(self, intent: str) -> Optional[str]:
        """
        获取意图对应的服务名称
        
        :param intent: 意图分类
        :return: 服务名称，不存在返回 None
        """
        route = self._routes.get(intent)
        return route["service_name"] if route else None
    
    def list_routes(self) -> List[Dict[str, Any]]:
        """获取所有路由规则"""
        result = []
        for intent, route in self._routes.items():
            result.append({
                "intent": intent,
                **route
            })
        return result
    
    def remove_route(self, intent: str) -> bool:
        """
        删除路由规则
        
        :param intent: 意图分类
        :return: 是否成功删除
        """
        if intent in self._routes:
            del self._routes[intent]
            return True
        return False


# 全局注册器实例
tool_registry = Registry("tools")
intent_registry = Registry("intents")
location_registry = Registry("locations")

# 全局路由实例
service_router = Router()
