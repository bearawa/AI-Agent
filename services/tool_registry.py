import time
import json
from typing import Dict, Any, List, Optional, Callable
import concurrent.futures
from utils.logger import logger
from repositories import sqlite_repository
from services.weather_tool import get_weather
from services.calendar_tool import get_school_calendar
from services.rag_service import RAGService

# 初始化 RAG 服务以供知识库检索工具使用
_rag_service = RAGService()

def search_campus_knowledge(query: str, optional_hint: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    """
    检索学校知识库，获取相关规章制度、办事指南和政策材料。
    """
    try:
        # 兼容老版 Agent 可能传的 category 或新版传的 optional_hint
        hint = optional_hint or category
        intent_conf = 1.0 if hint and hint != "other" else None
        
        # 使用 RAG 服务 retrieve 进行全库优先+分类加权的软检索
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
            return {
                "query": query,
                "message": "当前知识库未检索到足够相关资料。",
                "results": []
            }
            
        return {
            "query": query,
            "optional_hint": hint,
            "chunks_count": len(simplified_chunks),
            "results": simplified_chunks
        }
    except Exception as e:
        logger.error(f"工具检索知识库异常: {e}")
        return {
            "query": query,
            "error": str(e),
            "results": []
        }

def get_campus_service_status(service_name: str) -> Dict[str, Any]:
    """
    查询校园服务状态（如图书馆、食堂、校车等是否正常开放）。
    """
    services = {
        "图书馆": "正常开放。今日开放时间：08:00 - 22:00，自习室正常对外开放。",
        "食堂": "正常营业。一食堂、二食堂、三食堂均提供早中晚餐，目前非高峰期。",
        "校车": "正常运营。发车时间为 07:00 - 21:00，目前发车间隔为 15 分钟/班。",
        "校园网": "运行正常。今日无网费结算停网或割接割接通知。",
        "校医院": "正常接诊。急诊 24 小时值班，普通门诊时间：08:00 - 17:00。"
    }
    
    matched_key = None
    for k in services:
        if k in service_name:
            matched_key = k
            break
            
    if matched_key:
        return {
            "service_name": matched_key,
            "status": "正常",
            "detail": services[matched_key],
            "is_demo": True,
            "notice": "演示校园服务数据，仅用于项目功能展示"
        }
    else:
        return {
            "service_name": service_name,
            "status": "未知",
            "detail": f"未检索到“{service_name}”的实时状态，建议直接前往现场咨询或查看公告。",
            "is_demo": True,
            "notice": "演示校园服务数据，仅用于项目功能展示"
        }

# 工具注册字典
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "get_weather": {
        "name": "get_weather",
        "display_name": "天气查询工具",
        "func": get_weather,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询特定城市和日期的天气信息。如果用户没有指定城市，默认可以查询学校所在城市（如南京）的天气。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称，例如：南京、北京、上海。"
                        },
                        "date": {
                            "type": "string",
                            "description": "日期或相对日期描述，例如：今天、明天、后天、2026-07-09。"
                        }
                    },
                    "required": ["city", "date"]
                }
            }
        }
    },
    "get_school_calendar": {
        "name": "get_school_calendar",
        "display_name": "校历查询工具",
        "func": get_school_calendar,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_school_calendar",
                "description": "查询学校校历信息，如开学注册时间、放假安排、考试周等时间段规划。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "校历查询关键字，例如：开学、放假、考试、国庆节。"
                        }
                    }
                }
            }
        }
    },
    "get_campus_service_status": {
        "name": "get_campus_service_status",
        "display_name": "校园服务状态查询",
        "func": get_campus_service_status,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_campus_service_status",
                "description": "查询校园常用服务与设施（如图书馆、食堂、校车、校园网、校医院）的实时运营或开放状态。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "想要查询的校园服务名称，例如：图书馆、食堂、校车、校园网、校医院。"
                        }
                    },
                    "required": ["service_name"]
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
    """
    获取所有已注册工具的 JSON Schema，供 LLM 接口使用。
    """
    return [t["schema"] for t in TOOL_REGISTRY.values()]

def call_tool(
    name: str, 
    args: Dict[str, Any], 
    session_id: Optional[str] = None, 
    message_id: Optional[str] = None,
    timeout_seconds: float = 8.0
) -> Dict[str, Any]:
    """
    执行指定名称的工具，带 8 秒超时和异常捕获，并自动记录日志。
    """
    if name not in TOOL_REGISTRY:
        error_msg = f"未注册的工具名称: {name}"
        logger.error(error_msg)
        return {"success": False, "error_message": error_msg, "result": None}

    tool_def = TOOL_REGISTRY[name]
    func = tool_def["func"]
    display_name = tool_def["display_name"]
    
    start_time = time.time()
    success = 1
    error_message = None
    result_str = ""
    result_obj = None

    logger.info(f"开始执行工具 '{name}' ({display_name})，参数: {args}，超时时间: {timeout_seconds}秒")
    
    try:
        # 使用线程池加上超时控制执行工具
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, **args)
            result_obj = future.result(timeout=timeout_seconds)
            result_str = json.dumps(result_obj, ensure_ascii=False)
    except concurrent.futures.TimeoutError as te:
        success = 0
        error_message = f"工具执行超时 ({timeout_seconds}s)"
        logger.error(f"工具 '{name}' 执行超时: {te}")
        result_obj = {"error": error_message, "is_demo": True, "notice": "演示数据（执行超时）"}
        result_str = json.dumps(result_obj, ensure_ascii=False)
    except Exception as e:
        success = 0
        error_message = str(e)
        logger.error(f"工具 '{name}' 执行时发生异常: {e}")
        result_obj = {"error": f"工具执行失败: {error_message}", "is_demo": True, "notice": "演示数据（执行失败）"}
        result_str = json.dumps(result_obj, ensure_ascii=False)

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(f"工具 '{name}' 执行结束，成功: {success == 1}，耗时: {elapsed_ms}ms")

    # 写入 SQLite tool_logs 表中
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
        logger.error(f"记录工具日志到数据库失败: {dbe}")

    return {
        "success": success == 1,
        "result": result_obj,
        "elapsed_ms": elapsed_ms,
        "error_message": error_message
    }
