from typing import Optional
from repositories import sqlite_repository
from utils.logger import logger

def record_agent_trace(
    session_id: Optional[str],
    message_id: Optional[str],
    step_index: int,
    step_type: str,
    step_title: str,
    step_detail: str
) -> str:
    """
    保存并记录 Agent 执行轨迹步骤。
    
    :param session_id: 会话 ID
    :param message_id: 消息 ID
    :param step_index: 步骤序号（1-indexed）
    :param step_type: 步骤类型，如 "intent", "clarify", "tool_call", "tool_result", "rag_search", "final_response"
    :param step_title: 步骤简短名称，例如：“已识别复合问题”
    :param step_detail: 详细细节或中间日志
    :return: 写入的 trace_id
    """
    logger.info(f"[Agent Trace Step {step_index}] [{step_type}] {step_title} - {step_detail[:80]}...")
    try:
        trace_id = sqlite_repository.save_agent_trace(
            session_id=session_id,
            message_id=message_id,
            step_index=step_index,
            step_type=step_type,
            step_title=step_title,
            step_detail=step_detail
        )
        return trace_id
    except Exception as e:
        logger.error(f"记录 Agent 执行轨迹异常: {e}")
        return ""
