import time
import json
from typing import Dict, Any, List, Optional
import concurrent.futures
from utils.logger import logger
from repositories import sqlite_repository
from services.amap_tool import get_weather_amap, search_nearby_poi, plan_route
from services.rag_service import RAGService
from mapping.tool_mapper import tool_mapper

# 初始化 RAG 服务以供知识库检索工具使用
_rag_service = RAGService()

# 初始化工具映射器
def _initialize_tools():
    tool_mapper.register_tool(
        name="get_weather_amap",
        func=get_weather_amap,
        display_name="高德天气查询",
        description="通过高德地图 API 查询指定城市的真实天气信息（包括实时天气和天气预报）。支持查询今天/明天/后天的天气，以及任意城市名称。",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，例如：南京、北京、上海、杭州。"},
                "date": {"type": "string", "description": "日期或相对日期，例如：今天、明天、后天、2026-07-10。"}
            },
            "required": ["city", "date"]
        },
        category="amap"
    )
    
    tool_mapper.register_tool(
        name="search_nearby_poi",
        func=search_nearby_poi,
        display_name="周边设施搜索",
        description="基于学校位置搜索周边的兴趣点 (POI)，如附近的医院、银行、餐厅、超市、药店、公交站等设施。当用户询问学校附近有什么设施或要去某个地方时调用。",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词，例如：医院、银行、餐厅、超市、药店、公交站、地铁站。"},
                "radius": {"type": "integer", "description": "搜索半径（单位：米），默认 2000 米。可选值：500, 1000, 2000, 5000。"}
            },
            "required": ["keyword"]
        },
        category="amap"
    )
    
    tool_mapper.register_tool(
        name="plan_route",
        func=plan_route,
        display_name="路线规划导航",
        description="规划从起点到终点的步行或骑行路线。支持地点名称（如教学楼、图书馆）或坐标。当用户询问怎么去某个地方、路线怎么走时调用。",
        parameters={
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "起点名称或坐标，如：教学楼、图书馆、校门口。"},
                "destination": {"type": "string", "description": "终点名称或坐标，如：食堂、体育馆、南京南站。"},
                "mode": {"type": "string", "description": "出行方式：walking（步行，默认）、bicycling（骑行）。"}
            },
            "required": ["origin", "destination"]
        },
        category="amap"
    )
    
    tool_mapper.register_tool(
        name="search_campus_knowledge",
        func=search_campus_knowledge,
        display_name="校园知识库检索",
        description="检索学校知识库，获取相关规章制度、办事指南、新生报到要求和政策材料。在需要回答校园内各类政策或流程细节时调用。",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索关键词，例如：新生报到准备什么、奖学金申请条件、宿舍报修电话。"},
                "optional_hint": {"type": "string", "description": "（可选）对类别的加权排序提示：admission（招生）、academic（学务）、logistics（后勤）、campus_life（校园生活）。"}
            },
            "required": ["query"]
        },
        category="rag"
    )

def search_campus_knowledge(query: str, optional_hint: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    """
    检索学校知识库，获取相关规章制度、办事指南和政策材料。
    """
    try:
        hint = optional_hint or category
        intent_conf = 1.0 if hint and hint != "other" else None

        chunks = _rag_service.retrieve(
            query=query,
            intent=hint,
            intent_confidence=intent_conf,
            top_k=5,
            use_category_boost=True
        )

        simplified_chunks = []
        for c in chunks:
            page_info = f"第 {c['page_number']} 页" if c.get('page_number') is not None else f"片段 {c['chunk_index']}"
            simplified_chunks.append({
                "doc_id": c.get("doc_id", ""),
                "file_name": c["file_name"],
                "category_name": c.get("category_name", "未分类"),
                "page_number": c.get("page_number"),
                "chunk_index": c.get("chunk_index"),
                "page_info": page_info,
                "similarity_distance": c["similarity_distance"],
                "source_text": c["source_text"]
            })

        if not simplified_chunks:
            return {"query": query, "message": "当前知识库未检索到足够相关资料。", "results": []}

        return {
            "query": query, "optional_hint": hint,
            "chunks_count": len(simplified_chunks), "results": simplified_chunks
        }
    except Exception as e:
        logger.error(f"工具检索知识库异常: {e}")
        return {"query": query, "error": str(e), "results": []}


# 模块加载时自动初始化工具（在 search_campus_knowledge 定义之后）
_initialize_tools()


# 工具注册字典（仅真实数据工具）
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "get_weather_amap": {
        "name": "get_weather_amap",
        "display_name": "高德天气查询",
        "func": get_weather_amap,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_weather_amap",
                "description": "通过高德地图 API 查询指定城市的真实天气信息（包括实时天气和天气预报）。支持查询今天/明天/后天的天气，以及任意城市名称。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称，例如：南京、北京、上海、杭州。"
                        },
                        "date": {
                            "type": "string",
                            "description": "日期或相对日期，例如：今天、明天、后天、2026-07-10。"
                        }
                    },
                    "required": ["city", "date"]
                }
            }
        }
    },
    "search_nearby_poi": {
        "name": "search_nearby_poi",
        "display_name": "周边设施搜索",
        "func": search_nearby_poi,
        "schema": {
            "type": "function",
            "function": {
                "name": "search_nearby_poi",
                "description": "基于学校位置搜索周边的兴趣点 (POI)，如附近的医院、银行、餐厅、超市、药店、公交站等设施。当用户询问学校附近有什么设施或要去某个地方时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "搜索关键词，例如：医院、银行、餐厅、超市、药店、公交站、地铁站。"
                        },
                        "radius": {
                            "type": "integer",
                            "description": "搜索半径（单位：米），默认 2000 米。可选值：500, 1000, 2000, 5000。"
                        }
                    },
                    "required": ["keyword"]
                }
            }
        }
    },
    "plan_route": {
        "name": "plan_route",
        "display_name": "路线规划导航",
        "func": plan_route,
        "schema": {
            "type": "function",
            "function": {
                "name": "plan_route",
                "description": "规划从起点到终点的步行或骑行路线。支持地点名称（如教学楼、图书馆）或坐标。当用户询问怎么去某个地方、路线怎么走时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "起点名称或坐标，如：教学楼、图书馆、校门口。"
                        },
                        "destination": {
                            "type": "string",
                            "description": "终点名称或坐标，如：食堂、体育馆、南京南站。"
                        },
                        "mode": {
                            "type": "string",
                            "description": "出行方式：walking（步行，默认）、bicycling（骑行）。"
                        }
                    },
                    "required": ["origin", "destination"]
                }
            }
        }
    },
    "search_campus_knowledge": {
        "name": "search_campus_knowledge",
        "display_name": "校园知识库检索",
        "func": search_campus_knowledge,
        "schema": {
            "type": "function",
            "function": {
                "name": "search_campus_knowledge",
                "description": "检索学校知识库，获取相关规章制度、办事指南、新生报到要求和政策材料。在需要回答校园内各类政策或流程细节时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "检索关键词，例如：新生报到准备什么、奖学金申请条件、宿舍报修电话。"
                        },
                        "optional_hint": {
                            "type": "string",
                            "description": "（可选）对类别的加权排序提示：admission（招生）、academic（学务）、logistics（后勤）、campus_life（校园生活）。此提示只做相关度加权，系统仍会检索全库以防漏检。"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    }
}


def get_all_tool_schemas() -> List[Dict[str, Any]]:
    """获取所有已注册工具的 JSON Schema，供 LLM 接口使用。"""
    return tool_mapper.get_all_tool_schemas()


def call_tool(
    name: str,
    args: Dict[str, Any],
    session_id: Optional[str] = None,
    message_id: Optional[str] = None,
    timeout_seconds: float = 8.0
) -> Dict[str, Any]:
    """执行指定名称的工具，带 8 秒超时和异常捕获，并自动记录日志。"""
    if not tool_mapper.is_tool_registered(name):
        error_msg = f"未注册的工具名称: {name}"
        logger.error(error_msg)
        return {"success": False, "error_message": error_msg, "result": None}

    tool_def = tool_mapper.get_tool(name)
    func = tool_def["func"]
    display_name = tool_def["display_name"]

    start_time = time.time()
    success = 1
    error_message = None
    result_str = ""
    result_obj = None

    logger.info(f"开始执行工具 '{name}' ({display_name})，参数: {args}，超时时间: {timeout_seconds}秒")

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, **args)
            result_obj = future.result(timeout=timeout_seconds)
            result_str = json.dumps(result_obj, ensure_ascii=False)
    except concurrent.futures.TimeoutError as te:
        success = 0
        error_message = f"工具执行超时 ({timeout_seconds}s)"
        logger.error(f"工具 '{name}' 执行超时: {te}")
        result_obj = {"error": error_message, "is_demo": True, "notice": "执行超时"}
        result_str = json.dumps(result_obj, ensure_ascii=False)
    except Exception as e:
        success = 0
        error_message = str(e)
        logger.error(f"工具 '{name}' 执行时发生异常: {e}")
        result_obj = {"error": f"工具执行失败: {error_message}", "is_demo": True, "notice": "执行失败"}
        result_str = json.dumps(result_obj, ensure_ascii=False)

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(f"工具 '{name}' 执行结束，成功: {success == 1}，耗时: {elapsed_ms}ms")

    try:
        args_str = json.dumps(args, ensure_ascii=False)
        sqlite_repository.save_tool_log(
            tool_name=name, tool_display_name=display_name,
            tool_args=args_str, tool_result=result_str,
            success=success, elapsed_ms=elapsed_ms,
            session_id=session_id, message_id=message_id,
            error_message=error_message
        )
    except Exception as dbe:
        logger.error(f"记录工具日志到数据库失败: {dbe}")

    return {
        "success": success == 1,
        "result": result_obj,
        "elapsed_ms": elapsed_ms,
        "error_message": error_message
    }
