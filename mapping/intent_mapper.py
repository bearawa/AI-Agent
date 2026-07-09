# -*- coding: utf-8 -*-
"""
AIZS 意图映射器
管理意图分类到服务的路由映射，支持动态扩展。
"""
from typing import Dict, Any, List, Optional
from mapping.framework import service_router, intent_registry
from utils.logger import logger


class IntentMapper:
    """意图分类到服务的映射器"""
    
    INTENT_NAMES: Dict[str, str] = {
        "general": "通用资料",
        "admission": "招生",
        "academic": "学务",
        "logistics": "后勤",
        "campus_life": "校园生活",
        "weather": "天气查询",
        "navigation": "路线导航",
        "other": "其他"
    }
    
    INTENT_TO_SERVICE: Dict[str, str] = {
        "general": "rag_service",
        "admission": "rag_service",
        "academic": "rag_service",
        "logistics": "rag_service",
        "campus_life": "rag_service",
        "weather": "amap_service",
        "navigation": "amap_service",
        "other": "rag_service"
    }
    
    INTENT_DESCRIPTIONS: Dict[str, str] = {
        "general": "通用校园信息查询",
        "admission": "招生录取相关咨询",
        "academic": "教学教务相关咨询",
        "logistics": "后勤服务相关咨询",
        "campus_life": "校园生活相关咨询",
        "weather": "天气查询服务",
        "navigation": "路线导航服务",
        "other": "其他类型咨询"
    }
    
    def __init__(self):
        self._initialize_registry()
    
    def _initialize_registry(self):
        """初始化意图注册表和路由"""
        for intent, name in self.INTENT_NAMES.items():
            intent_registry.register(
                key=intent,
                item=intent,
                metadata={
                    "name": name,
                    "description": self.INTENT_DESCRIPTIONS.get(intent, ""),
                    "service": self.INTENT_TO_SERVICE.get(intent, "rag_service")
                }
            )
            service_router.add_route(
                intent=intent,
                service_name=self.INTENT_TO_SERVICE.get(intent, "rag_service")
            )
        
        logger.info("意图映射器初始化完成")
    
    def get_intent_name(self, intent: str) -> str:
        """获取意图的中文名称"""
        return self.INTENT_NAMES.get(intent, "其他")
    
    def get_service_name(self, intent: str) -> str:
        """获取意图对应的服务名称"""
        return self.INTENT_TO_SERVICE.get(intent, "rag_service")
    
    def route(self, intent: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """根据意图查找路由"""
        return service_router.route(intent, context)
    
    def list_intents(self) -> List[Dict[str, Any]]:
        """获取所有意图分类"""
        result = []
        for intent in self.INTENT_NAMES:
            result.append({
                "intent": intent,
                "name": self.INTENT_NAMES[intent],
                "description": self.INTENT_DESCRIPTIONS.get(intent, ""),
                "service": self.INTENT_TO_SERVICE.get(intent, "rag_service")
            })
        return result
    
    def add_intent(self, intent: str, name: str, service: str = "rag_service", description: str = ""):
        """
        添加新的意图分类
        
        :param intent: 意图标识
        :param name: 中文名称
        :param service: 对应服务名称
        :param description: 描述
        """
        if intent in self.INTENT_NAMES:
            logger.warning(f"意图 '{intent}' 已存在，将被更新")
        
        self.INTENT_NAMES[intent] = name
        self.INTENT_TO_SERVICE[intent] = service
        self.INTENT_DESCRIPTIONS[intent] = description
        
        intent_registry.register(
            key=intent,
            item=intent,
            metadata={
                "name": name,
                "description": description,
                "service": service
            }
        )
        service_router.add_route(intent=intent, service_name=service)
        
        logger.info(f"添加新意图: {intent} -> {name}")
    
    def remove_intent(self, intent: str) -> bool:
        """
        删除意图分类
        
        :param intent: 意图标识
        :return: 是否成功删除
        """
        if intent not in self.INTENT_NAMES:
            return False
        
        del self.INTENT_NAMES[intent]
        del self.INTENT_TO_SERVICE[intent]
        if intent in self.INTENT_DESCRIPTIONS:
            del self.INTENT_DESCRIPTIONS[intent]
        
        intent_registry.unregister(intent)
        service_router.remove_route(intent)
        
        logger.info(f"删除意图: {intent}")
        return True
    
    def is_valid_intent(self, intent: str) -> bool:
        """检查意图是否有效"""
        return intent in self.INTENT_NAMES


# 全局意图映射器实例
intent_mapper = IntentMapper()
