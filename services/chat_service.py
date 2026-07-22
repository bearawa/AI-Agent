import json
import time
from typing import List, Dict, Any, Generator
from config import settings
from utils.logger import logger
from repositories import sqlite_repository
from services.llm_service import LLMService
from services.rag_service import RAGService
from services.intent_service import IntentService
from services.tool_registry import call_tool, get_all_tool_schemas


class ChatService:
    def __init__(self):
        self.llm_service = LLMService()
        self.rag_service = RAGService()
        self.intent_service = IntentService()

    def start_new_session(self, title: str = "新建会话") -> str:
        return sqlite_repository.create_chat_session(title)

    def _try_tool_calls(
        self,
        history: List[Dict[str, str]],
        current_query: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        通过 LLM Function Calling 判断用户提问是否需要调用工具。
        需要则执行并返回工具结果列表，不需要则返回空列表。
        """
        tool_schemas = get_all_tool_schemas()
        if not tool_schemas:
            return []

        system_prompt = f"""你是中南财经政法大学校园智能咨询助手的工具调度模块。
你的唯一职责是：判断用户提问是否需要调用工具获取实时数据，如果需要就调用对应工具，如果不需要就直接回复"不需要调用工具"。

【工具调用规则】
1. 用户问天气相关（天气、温度、下雨、气温、带伞等）→ 调用 get_weather_amap，城市默认"{settings.AMAP_DEFAULT_CITY}"
2. 用户问学校周边设施（附近哪里有医院/银行/餐厅/超市/药店等）→ 调用 search_nearby_poi
3. 用户问路线导航（怎么走、怎么去、路线、步行到某处等）→ 调用 plan_route
4. 其他问题（学校政策、规章制度、招生、选课、奖学金等）→ 不调用工具

【重要】
- 只做工具调度判断，不要回答用户的问题。
- 不需要调用工具时，只回复"不需要调用工具"，不要输出其他内容。"""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": current_query})

        try:
            response = self.llm_service.client.chat.completions.create(
                model=self.llm_service.model,
                messages=messages,
                tools=tool_schemas,
                tool_choice="auto",
                temperature=0.1,
                max_tokens=500
            )
            response_msg = response.choices[0].message
            tool_calls = response_msg.tool_calls

            if not tool_calls:
                logger.info(f"ChatService LLM 判断不需要工具调用，提问: '{current_query}'")
                return []

            tool_results = []
            for tc in tool_calls:
                func_name = tc.function.name
                func_args = {}
                try:
                    func_args = json.loads(tc.function.arguments)
                except Exception as e:
                    logger.warning(f"ChatService 解析工具参数失败 (func_name={func_name}): {e}")

                logger.info(f"ChatService Function Calling 触发工具: {func_name}({func_args})")
                tool_res = call_tool(name=func_name, args=func_args, session_id=session_id, message_id=None)
                tool_results.append({
                    "name": func_name, "args": func_args,
                    "result": tool_res.get("result"),
                    "success": tool_res.get("success", False)
                })
            return tool_results

        except Exception as e:
            logger.error(f"ChatService Function Calling 检测失败: {e}")
            return []

    def handle_chat_flow(
        self,
        session_id: str,
        user_content: str
    ) -> Generator[Dict[str, Any], None, None]:
        """
        核心 RAG 聊天问答流，整合意图分类、工具调用、知识库检索和流式生成。
        """
        start_time = time.time()

        # 1. 意图识别
        intent_res = self.intent_service.classify_intent(user_content)
        intent = intent_res["intent"]
        intent_name = self.intent_service.intent_names.get(intent, "其他")
        intent_confidence = intent_res["confidence"]
        intent_reason = intent_res["reason"]

        yield {"type": "intent", "data": {
            "intent": intent, "intent_name": intent_name,
            "confidence": intent_confidence, "reason": intent_reason
        }}

        # 2. 保存用户消息
        user_msg_id = sqlite_repository.save_message(
            session_id=session_id, role="user", content=user_content
        )

        # 3. 更新会话标题
        history_msgs = sqlite_repository.get_chat_messages(session_id)
        user_msgs_only = [m for m in history_msgs if m["role"] == "user"]
        if len(user_msgs_only) == 1:
            new_title = user_content.strip()[:15]
            if len(user_content) > 15:
                new_title += "..."
            sqlite_repository.update_session_title(session_id, new_title)

        # 4. 读取历史
        recent_history = sqlite_repository.get_chat_messages(session_id, limit=settings.MAX_HISTORY_MESSAGES + 1)
        recent_history = [m for m in recent_history if m["message_id"] != user_msg_id]
        formatted_history = [{"role": m["role"], "content": m["content"]} for m in recent_history]

        # 5. 改写检索词
        rewritten_query = self.llm_service.rewrite_query(formatted_history, user_content)

        # 6. 尝试工具调用（天气/POI/路线规划等）
        tool_results = self._try_tool_calls(formatted_history, user_content, session_id)

        # 7. RAG 知识库检索
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

        yield {"type": "sources", "data": retrieved_chunks}

        # 8. 构建包含工具结果的上下文，流式生成回答
        full_response = ""
        try:
            for text_chunk in self._generate_answer_stream(
                history=formatted_history,
                retrieved_chunks=retrieved_chunks,
                tool_results=tool_results,
                current_query=user_content,
                intent=intent_name,
                intent_confidence=intent_confidence
            ):
                full_response += text_chunk
                yield {"type": "text", "data": text_chunk}
        except Exception as e:
            logger.error(f"流式获取助手回答失败: {e}")
            yield {"type": "error", "data": f"获取回答时发生异常: {str(e)}"}
            return

        response_time_ms = int((time.time() - start_time) * 1000)

        # 9. 保存助手消息
        if full_response.strip():
            assistant_msg_id = sqlite_repository.save_message(
                session_id=session_id, role="assistant", content=full_response,
                intent=intent, intent_name=intent_name,
                intent_confidence=intent_confidence, intent_reason=intent_reason,
                rewritten_query=rewritten_query,
                has_source=1 if retrieved_chunks else 0,
                response_time_ms=response_time_ms,
                tool_used=1 if tool_results else 0
            )
            if retrieved_chunks:
                sources_to_save = []
                for chunk in retrieved_chunks:
                    sources_to_save.append({
                        "doc_id": chunk["doc_id"], "chunk_id": chunk["chunk_id"],
                        "file_name": chunk["file_name"], "page_number": chunk["page_number"],
                        "chunk_index": chunk["chunk_index"], "source_text": chunk["source_text"],
                        "similarity_distance": chunk["similarity_distance"]
                    })
                sqlite_repository.save_message_sources(assistant_msg_id, sources_to_save)

    def _generate_answer_stream(
        self,
        history: List[Dict[str, str]],
        retrieved_chunks: List[Dict[str, Any]],
        tool_results: List[Dict[str, Any]],
        current_query: str,
        intent: str = None,
        intent_confidence: float = None
    ) -> Generator[str, None, None]:
        """
        基于知识库检索结果 + 工具调用结果，流式生成最终回答。
        """
        # 知识库上下文
        context_str = ""
        if retrieved_chunks:
            for chunk in retrieved_chunks:
                page_info = f"第 {chunk['page_number']} 页" if chunk.get('page_number') is not None else f"片段 {chunk['chunk_index']}"
                chunk_cat = chunk.get("category_name", "未分类")
                context_str += f"--- 资料来源：{chunk['file_name']} ({page_info}) | 分类：{chunk_cat} ---\n"
                context_str += f"{chunk['source_text']}\n\n"
        else:
            context_str = "（当前未检索到任何相关的参考资料）"

        # 工具结果上下文
        tool_context = ""
        if tool_results:
            for tr in tool_results:
                tool_context += f"\n【{tr['name']} 调用结果】\n"
                tool_context += json.dumps(tr["result"], ensure_ascii=False, indent=2) + "\n"

        system_prompt = """你是中南财经政法大学校园智能咨询平台的助手，服务于在校学生、家长与教职工。
你必须依据【知识库检索结果】和【工具调用结果】来回答用户问题。

重要规则：
1. 如果有工具调用结果（如天气数据、周边设施、路线规划），请优先使用这些真实数据来回答。
2. 如果知识库有相关内容，结合知识库和工具结果综合回答。
3. 如果知识库中没有依据且没有工具结果，请明确说明"当前知识库未检索到相关依据"，不要编造信息。
4. 回答语言简明易懂，适合学生和家长阅读，使用 Markdown 排版。"""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        conf_val = intent_confidence if intent_confidence is not None else 0.0
        user_msg = f"""【意图识别结果】
intent: {intent or 'other'}
confidence: {conf_val:.2f}

【知识库检索结果】
{context_str}"""

        if tool_context:
            user_msg += f"""
【工具调用结果】
{tool_context}"""

        user_msg += f"""
【当前问题】
{current_query}"""
        messages.append({"role": "user", "content": user_msg})

        logger.info("开始调用 LLM 流式生成回答（含工具结果）...")
        stream = self.llm_service.client.chat.completions.create(
            model=self.llm_service.model,
            messages=messages,
            temperature=0.3,
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
