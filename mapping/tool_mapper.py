# -*- coding: utf-8 -*-
"""
AIZS 工具映射器
管理工具的注册、调用和元数据管理，支持动态扩展。
"""
import time
import json
from typing import Dict, Any, List, Optional, Callable
from mapping.framework import tool_registry
from repositories import sqlite_repository
from utils.logger import logger


class ToolMapper:
    """工具注册和调用管理器"""
    
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        display_name: str,
        description: str,
        parameters: Dict[str, Any],
        category: str = "general"
    ):
        """
        注册一个工具
        
        :param name: 工具唯一标识
        :param func: 工具函数
        :param display_name: 显示名称
        :param description: 功能描述
        :param parameters: 参数定义（符合 OpenAI Function Calling 格式）
        :param category: 工具分类
        """
        if name in self._tools:
            logger.warning(f"工具 '{name}' 已存在，将被覆盖")
        
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }
        
        self._tools[name] = {
            "name": name,
            "func": func,
            "display_name": display_name,
            "description": description,
            "parameters": parameters,
            "category": category,
            "schema": schema
        }
        
        tool_registry.register(
            key=name,
            item=func,
            metadata={
                "display_name": display_name,
                "description": description,
                "parameters": parameters,
                "category": category,
                "schema": schema
            }
        )
        
        logger.info(f"注册工具: {name} -> {display_name}")
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息
        
        :param name: 工具名称
        :return: 工具信息字典，未找到返回 None
        """
        return self._tools.get(name)
    
    def get_tool_func(self, name: str) -> Optional[Callable]:
        """
        获取工具函数
        
        :param name: 工具名称
        :return: 工具函数，未找到返回 None
        """
        tool = self._tools.get(name)
        return tool["func"] if tool else None
    
    def get_tool_display_name(self, name: str) -> str:
        """
        获取工具显示名称
        
        :param name: 工具名称
        :return: 显示名称，未找到返回原名称
        """
        tool = self._tools.get(name)
        return tool["display_name"] if tool else name
    
    def call_tool(
        self,
        name: str,
        args: Dict[str, Any],
        session_id: Optional[str] = None,
        message_id: Optional[str] = None,
        timeout_seconds: float = 8.0
    ) -> Dict[str, Any]:
        """
        执行工具调用
        
        :param name: 工具名称
        :param args: 工具参数
        :param session_id: 会话 ID
        :param message_id: 消息 ID
        :param timeout_seconds: 超时时间
        :return: 执行结果字典
        """
        tool = self._tools.get(name)
        if not tool:
            error_msg = f"未注册的工具: {name}"
            logger.error(error_msg)
            return {"success": False, "error_message": error_msg, "result": None}
        
        func = tool["func"]
        display_name = tool["display_name"]
        
        start_time = time.time()
        success = 1
        error_message = None
        result_str = ""
        result_obj = None
        
        logger.info(f"执行工具 '{name}' ({display_name})，参数: {args}")
        
        try:
            result_obj = func(**args)
            result_str = json.dumps(result_obj, ensure_ascii=False)
        except Exception as e:
            success = 0
            error_message = str(e)
            logger.error(f"工具 '{name}' 执行异常: {e}")
            result_obj = {"error": f"工具执行失败: {error_message}", "is_demo": True, "notice": "执行失败"}
            result_str = json.dumps(result_obj, ensure_ascii=False)
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"工具 '{name}' 执行完成，成功: {success == 1}，耗时: {elapsed_ms}ms")
        
        try:
            args_str = json.dumps(args, ensure_ascii=False)
            sqlite_repository.save_tool_log(
                tool_name=name,
                tool_display_name=display_name,
                tool_args=args_str,
                tool_result=result_str,
                success=success,
                elapsed_ms=elapsed_ms,
                session_id=session_id,
                message_id=message_id,
                error_message=error_message
            )
        except Exception as dbe:
            logger.error(f"记录工具日志失败: {dbe}")
        
        return {
            "success": success == 1,
            "result": result_obj,
            "elapsed_ms": elapsed_ms,
            "error_message": error_message
        }
    
    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 JSON Schema"""
        return [tool["schema"] for tool in self._tools.values()]
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """获取所有注册工具列表"""
        result = []
        for name, tool in self._tools.items():
            result.append({
                "name": name,
                "display_name": tool["display_name"],
                "description": tool["description"],
                "category": tool["category"],
                "parameters": tool["parameters"]
            })
        return result
    
    def list_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按分类获取工具列表"""
        result = []
        for name, tool in self._tools.items():
            if tool["category"] == category:
                result.append({
                    "name": name,
                    "display_name": tool["display_name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                })
        return result
    
    def unregister_tool(self, name: str) -> bool:
        """
        注销工具
        
        :param name: 工具名称
        :return: 是否成功注销
        """
        if name in self._tools:
            del self._tools[name]
            tool_registry.unregister(name)
            logger.info(f"注销工具: {name}")
            return True
        return False
    
    def is_tool_registered(self, name: str) -> bool:
        """检查工具是否已注册"""
        return name in self._tools


# 全局工具映射器实例
tool_mapper = ToolMapper()
