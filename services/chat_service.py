import time
from typing import List, Dict, Any, Generator
from config import settings
from utils.logger import logger
from repositories import sqlite_repository
from services.llm_service import LLMService
from services.rag_service import RAGService
from services.intent_service import IntentService

class ChatService:
    def __init__(self):
        """
        初始化对话服务。
        """
        self.llm_service = LLMService()
        self.rag_service = RAGService()
        self.intent_service = IntentService()

    def start_new_session(self, title: str = "新建会话") -> str:
        """
        创建并返回一个新会话的 ID。
        """
        return sqlite_repository.create_chat_session(title)

    def handle_chat_flow(
        self,
        session_id: str,
        user_content: str
    ) -> Generator[Dict[str, Any], None, None]:
        """
        核心 RAG 聊天问答流，整合历史获取、意图分类、检索改写、分类过滤匹配和流式生成。
        """
        # 记录处理开始时间，计算 response_time_ms
        start_time = time.time()

        # 1. 对用户提问进行意图识别
        intent_res = self.intent_service.classify_intent(user_content)
        intent = intent_res["intent"]
        intent_name = self.intent_service.intent_names.get(intent, "其他")
        intent_confidence = intent_res["confidence"]
        intent_reason = intent_res["reason"]

        # 先向前端发送识别到的意图，使其能够在界面流式前进行展示
        yield {
            "type": "intent",
            "data": {
                "intent": intent,
                "intent_name": intent_name,
                "confidence": intent_confidence,
                "reason": intent_reason
            }
        }

        # 2. 保存用户的提问到关系库
        user_msg_id = sqlite_repository.save_message(
            session_id=session_id,
            role="user",
            content=user_content
        )
        
        # 3. 如果当前会话标题是默认值，尝试以用户首个问题的前15个字更新会话标题
        history_msgs = sqlite_repository.get_chat_messages(session_id)
        user_msgs_only = [m for m in history_msgs if m["role"] == "user"]
        if len(user_msgs_only) == 1:
            new_title = user_content.strip()[:15]
            if len(user_content) > 15:
                new_title += "..."
            sqlite_repository.update_session_title(session_id, new_title)
            logger.info(f"会话 {session_id} 接收到首条消息，标题已更新为: '{new_title}'")

        # 4. 读取最近的 6 条历史消息，用于改写检索词
        recent_history = sqlite_repository.get_chat_messages(session_id, limit=settings.MAX_HISTORY_MESSAGES + 1)
        recent_history = [m for m in recent_history if m["message_id"] != user_msg_id]
        
        formatted_history = [
            {"role": m["role"], "content": m["content"]}
            for m in recent_history
        ]

        # 5. 对问题进行改写
        rewritten_query = self.llm_service.rewrite_query(formatted_history, user_content)

        # 6. 检索知识库（采用全库优先 + 分类增强 + 通用资料补充 + 自动回退策略）
        retrieved_chunks = []
        try:
            retrieved_chunks = self.rag_service.retrieve(
                query=rewritten_query,
                intent=intent,
                intent_confidence=intent_confidence,
                top_k=settings.RAG_TOP_K,
                use_category_boost=True
            )
        except Exception as e:
            logger.error(f"检索向量库失败: {e}")
            retrieved_chunks = []

        # 7. 向前端返回最终选用的检索源数据
        yield {"type": "sources", "data": retrieved_chunks}

        # 8. 流式回答
        full_response = ""
        try:
            response_generator = self.llm_service.chat_stream(
                history=formatted_history,
                retrieved_chunks=retrieved_chunks,
                current_query=user_content,
                intent=intent_name,
                intent_confidence=intent_confidence
            )
            for text_chunk in response_generator:
                full_response += text_chunk
                yield {"type": "text", "data": text_chunk}
        except Exception as e:
            logger.error(f"流式获取助手回答失败: {e}")
            yield {"type": "error", "data": f"获取回答时发生异常: {str(e)}"}
            return

        # 计算耗时毫秒数
        response_time_ms = int((time.time() - start_time) * 1000)

        # 9. 回答流生成完毕，将完整回答及统计数据存入关系数据库
        if full_response.strip():
            assistant_msg_id = sqlite_repository.save_message(
                session_id=session_id,
                role="assistant",
                content=full_response,
                intent=intent,
                intent_name=intent_name,
                intent_confidence=intent_confidence,
                intent_reason=intent_reason,
                rewritten_query=rewritten_query,
                has_source=1 if retrieved_chunks else 0,
                response_time_ms=response_time_ms
            )
            
            # 10. 将检索到的切片存入 SQLite 来源表
            if retrieved_chunks:
                sources_to_save = []
                for chunk in retrieved_chunks:
                    sources_to_save.append({
                        "doc_id": chunk["doc_id"],
                        "chunk_id": chunk["chunk_id"],
                        "file_name": chunk["file_name"],
                        "page_number": chunk["page_number"],
                        "chunk_index": chunk["chunk_index"],
                        "source_text": chunk["source_text"],
                        "similarity_distance": chunk["similarity_distance"]
                    })
                sqlite_repository.save_message_sources(assistant_msg_id, sources_to_save)
                logger.info(f"已成功在 SQLite 中保存消息 {assistant_msg_id} 的 {len(sources_to_save)} 个原文来源记录")
