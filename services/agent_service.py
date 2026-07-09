import time
import json
from typing import Generator, Dict, Any, List, Optional
from openai import OpenAI
from config import settings
from utils.logger import logger
from repositories import sqlite_repository
from services.llm_service import LLMService
from services.rag_service import RAGService
from services.intent_service import IntentService
from services.tool_registry import call_tool, get_all_tool_schemas
from services.agent_trace_service import record_agent_trace
from services.quality_service import QualityService

class AgentService:
    def __init__(self):
        """
        初始化 Agent 服务。
        """
        self.llm_service = LLMService()
        self.rag_service = RAGService()
        self.intent_service = IntentService()
        self.quality_service = QualityService()
        
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.model = settings.CHAT_MODEL
        self._client = None

    @property
    def client(self) -> OpenAI:
        if not self.api_key:
            raise ValueError("未检测到 API 密钥，请在 .env 文件中配置 DASHSCOPE_API_KEY。")
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client

    def check_clarification(self, query: str, history: List[Dict[str, Any]]) -> Optional[str]:
        """
        根据规则判定当前提问是否需要澄清。
        
        规则：
        1. 模糊问题：["什么时候报名？", "需要什么材料？", "在哪里办理？", "可以申请吗？", "怎么缴费？"]
        2. 如果提问属于这些模糊问题之一：
           - 检查会话历史中是否有明确的上下文对象（例如包含“招生”、“奖学金”、“报到”等）。
           - 如果有，则不进行澄清拦截，交由后续 RAG/Agent 继续处理。
           - 如果没有，则返回特定的澄清追问语句。
        """
        # 标准化查询
        q = query.strip().replace("?", "？").lower()
        
        # 常见模糊问题前缀或精确匹配映射
        ambiguous_rules = {
            "报名": {
                "keywords": ["什么时候报名", "什么时候可以报名", "何时报名", "怎么报名"],
                "reply": "请问您咨询的是本科招生报名、研究生报名，还是校内活动报名？"
            },
            "材料": {
                "keywords": ["需要什么材料", "准备什么材料", "需要带什么材料", "带什么材料"],
                "reply": "请问您咨询的是新生报到入学准备材料、奖学金申请材料，还是转专业申请材料？"
            },
            "地点": {
                "keywords": ["在哪里办理", "在哪里办", "办手续在哪里", "去哪里办理"],
                "reply": "请问您咨询的是一卡通补办、宿舍入住登记，还是户口迁移手续的办理地点？"
            },
            "申请": {
                "keywords": ["可以申请吗", "怎么申请", "如何申请"],
                "reply": "请问您咨询的是贫困生助学金申请、勤工俭学岗位申请，还是缓交学费申请？"
            },
            "缴费": {
                "keywords": ["怎么缴费", "怎么交钱", "在哪里缴费", "如何交学费"],
                "reply": "请问您咨询的是学费缴纳、校园一卡通充值，还是宿舍水费电费的缴费方式？"
            }
        }
        
        # 匹配用户模糊问题
        matched_rule = None
        for rule_key, rule_val in ambiguous_rules.items():
            for kw in rule_val["keywords"]:
                if kw in q:
                    matched_rule = rule_val
                    break
            if matched_rule:
                break
                
        if not matched_rule:
            return None
            
        # 校验上下文对象是否明确
        # 检查最近 4 轮历史消息，看看是否提及过关键领域词
        has_context = False
        context_keywords = ["招生", "高考", "研究生", "活动", "社团", "迎新", "报到", "入学", "新生", "奖学金", "助学金", "转专业", "一卡通", "校园卡", "补办", "宿舍", "退宿", "报修", "缴费", "交费", "学费"]
        
        for msg in reversed(history[-6:]):
            content = msg.get("content", "")
            for kw in context_keywords:
                if kw in content:
                    has_context = True
                    logger.info(f"澄清追问检测：命中上下文关键词 '{kw}'，取消澄清拦截。")
                    break
            if has_context:
                break
                
        if has_context:
            return None
            
        # 没有上下文，触发澄清
        return matched_rule["reply"]

    def handle_agent_chat_flow(
        self,
        session_id: str,
        user_content: str
    ) -> Generator[Dict[str, Any], None, None]:
        """
        核心 Agent 运行流。支持复合提问拆分、工具调用循环（最长3轮）、澄清拦截、轨迹存储与流式最终应答。
        
        Yield 格式:
        - {"type": "intent", "data": {...}}
        - {"type": "trace", "data": {"step_title": "...", "step_detail": "..."}}
        - {"type": "sources", "data": [...] }
        - {"type": "text", "data": "..."}
        """
        start_time = time.time()
        
        # 1. 意图分类与用户消息落库
        intent_res = self.intent_service.classify_intent(user_content)
        intent = intent_res["intent"]
        intent_name = self.intent_service.intent_names.get(intent, "其他")
        
        yield {
            "type": "intent",
            "data": {
                "intent": intent,
                "intent_name": intent_name,
                "confidence": intent_res["confidence"],
                "reason": intent_res["reason"]
            }
        }
        
        # 先保存用户消息
        user_msg_id = sqlite_repository.save_message(
            session_id=session_id,
            role="user",
            content=user_content
        )
        
        # 2. 读取最近历史消息
        history_msgs = sqlite_repository.get_chat_messages(session_id)
        # 排除当前刚保存的 user 消息
        recent_history = [m for m in history_msgs if m["message_id"] != user_msg_id]
        
        # 3. 澄清追问检测
        clarification_reply = self.check_clarification(user_content, recent_history)
        if clarification_reply:
            step_idx = 1
            record_agent_trace(
                session_id=session_id,
                message_id=None, # 待生成助手消息后关联
                step_index=step_idx,
                step_type="clarify",
                step_title="已拦截模糊提问",
                step_detail=f"提问 '{user_content}' 缺少必要上下文，触发主动澄清追问。"
            )
            
            # 生成客服回答
            elapsed_ms = int((time.time() - start_time) * 1000)
            assistant_msg_id = sqlite_repository.save_message(
                session_id=session_id,
                role="assistant",
                content=clarification_reply,
                intent=intent,
                intent_name=intent_name,
                intent_confidence=intent_res["confidence"],
                intent_reason=intent_res["reason"],
                rewritten_query=user_content,
                has_source=0,
                response_time_ms=elapsed_ms,
                agent_mode=1,
                tool_used=0
            )
            
            # 更新 trace 的 message_id
            sqlite_repository.save_agent_trace(
                session_id=session_id,
                message_id=assistant_msg_id,
                step_index=step_idx,
                step_type="clarify",
                step_title="触发主动澄清追问",
                step_detail=clarification_reply
            )
            
            yield {
                "type": "trace",
                "data": {
                    "step_index": step_idx,
                    "step_type": "clarify",
                    "step_title": "触发主动澄清追问",
                    "step_detail": f"拦截模糊问题，追问具体咨询对象。"
                }
            }
            
            # 流式返回最终结果
            for char in clarification_reply:
                time.sleep(0.02)
                yield {"type": "text", "data": char}
                
            # 执行回答质量评估 (澄清通常属于高质量交互，因为能避免胡编乱造)
            try:
                self.quality_service.evaluate_and_save(
                    message_id=assistant_msg_id,
                    session_id=session_id,
                    query=user_content,
                    answer=clarification_reply,
                    sources=[],
                    tool_logs=[]
                )
            except Exception as qe:
                logger.error(f"对澄清回复进行质量评估异常: {qe}")
                
            return

        # 4. 进入 Agent 执行多步推理流程
        step_idx = 1
        record_agent_trace(
            session_id=session_id,
            message_id=None,
            step_index=step_idx,
            step_type="analyze",
            step_title="正在分析提问意图",
            step_detail=f"意图分类：{intent_name}。准备加载已注册的工具。"
        )
        yield {
            "type": "trace",
            "data": {
                "step_index": step_idx,
                "step_type": "analyze",
                "step_title": "正在分析提问意图",
                "step_detail": f"识别分类为【{intent_name}】，准备运行推理流程。"
            }
        }
        
        # 检查是否为复合问题
        is_composite = "新生报到" in user_content and ("天气" in user_content or "校历" in user_content) or ("和" in user_content and ("天气" in user_content or "开学" in user_content))
        if is_composite:
            step_idx += 1
            record_agent_trace(
                session_id=session_id,
                message_id=None,
                step_index=step_idx,
                step_type="composite_detect",
                step_title="已识别复合问题",
                step_detail=f"检测到复合式提问，将启动多步工具推理逻辑。"
            )
            yield {
                "type": "trace",
                "data": {
                    "step_index": step_idx,
                    "step_type": "composite_detect",
                    "step_title": "已识别复合问题",
                    "step_detail": "已识别出当前包含多个独立的咨询点，需拆分执行检索。"
                }
            }

        # 5. 组装 messages 供 LLM Agent 推理
        agent_system = """你是一个智能的校园问答 Agent 助手。你的目标是协助解答学生与家长的各种校园咨询。
你拥有一些工具可用。如果用户的提问需要通过工具获取数据（例如天气状况、校历安排、校园服务的开放状态或检索知识库内容），请调用对应的工具。
你可以根据需要同时调用多个工具，或者根据前一步的执行结果在下一轮调用新工具。

【必须遵守的规则】
1. 只根据工具返回的真实参考数据来生成最后的回答。如果工具没能查到足够的信息，请老实说明，绝不编造任何电话、地址或时间！
2. 如果没有任何工具返回有效参考，并且知识库检索也无匹配，请明确回复：“当前知识库未检索到相关依据”，不得任意发挥。
3. 绝对不要向用户展示你的 Agent 执行轨迹、隐藏的推理过程（如 <thought> 或 CoT 标记），仅输出你最终归纳给用户的简洁、亲切的中文回答。
"""
        messages = [{"role": "system", "content": agent_system}]
        
        # 加上最近 6 条历史消息
        for m in recent_history[-6:]:
            messages.append({"role": m["role"], "content": m["content"]})
            
        # 加上当前用户提问
        messages.append({"role": "user", "content": user_content})

        tools_schemas = get_all_tool_schemas()
        
        # 工具循环调用最大轮数
        max_loops = 3
        loop_count = 0
        tool_used_count = 0
        executed_tool_logs = []
        retrieved_rag_sources = []
        
        # 用于跟踪本次会话新产生的 trace 记录
        new_traces = []

        while loop_count < max_loops:
            loop_count += 1
            logger.info(f"Agent 推理第 {loop_count} 轮开始...")
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools_schemas,
                    tool_choice="auto",
                    temperature=0.2
                )
            except Exception as e:
                logger.error(f"Agent 调用大模型出错: {e}")
                yield {"type": "error", "data": f"Agent推理大模型服务异常: {str(e)}"}
                return
                
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # 若不需要工具调用，直接跳出循环，输出文本回答
            if not tool_calls:
                break
                
            # 将模型的回答存入消息列表
            messages.append(response_message)
            
            # 顺序执行工具调用
            for tool_call in tool_calls:
                tool_used_count += 1
                func_name = tool_call.function.name
                func_args = {}
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except Exception as je:
                    logger.warning(f"工具参数 JSON 解析失败: {je}")
                
                tool_display = func_name
                if func_name == "get_weather":
                    tool_display = "天气查询工具"
                elif func_name == "get_school_calendar":
                    tool_display = "校历查询工具"
                elif func_name == "get_campus_service_status":
                    tool_display = "校园服务状态查询"
                elif func_name == "search_campus_knowledge":
                    tool_display = "校园知识库检索"

                # 运行 trace 标记
                step_idx += 1
                trace_item = {
                    "step_index": step_idx,
                    "step_type": "tool_call",
                    "step_title": f"正在调用{tool_display}",
                    "step_detail": f"参数: {json.dumps(func_args, ensure_ascii=False)}"
                }
                new_traces.append(trace_item)
                yield {"type": "trace", "data": trace_item}
                
                # 执行工具
                tool_res = call_tool(
                    name=func_name,
                    args=func_args,
                    session_id=session_id,
                    message_id=None # 稍后在完成最终生成后关联
                )
                
                # 记录已运行的工具
                executed_tool_logs.append({
                    "name": func_name,
                    "display_name": tool_display,
                    "args": func_args,
                    "success": tool_res["success"],
                    "elapsed_ms": tool_res["elapsed_ms"],
                    "error_message": tool_res["error_message"],
                    "result": tool_res["result"]
                })
                
                # 提取 RAG 的匹配切片来源
                if func_name == "search_campus_knowledge" and tool_res["success"]:
                    results = tool_res["result"].get("results", [])
                    for r in results:
                        retrieved_rag_sources.append({
                            "doc_id": r["doc_id"],
                            "chunk_id": "", # 兼容
                            "file_name": r["file_name"],
                            "page_number": int(r["page_info"].replace("第", "").replace("页", "")) if "页" in r["page_info"] else None,
                            "chunk_index": 0,
                            "source_text": r["source_text"],
                            "similarity_distance": r["similarity_distance"]
                        })

                # 工具结果 trace
                step_idx += 1
                res_summary = str(tool_res["result"])
                if len(res_summary) > 200:
                    res_summary = res_summary[:200] + "..."
                    
                trace_res_item = {
                    "step_index": step_idx,
                    "step_type": "tool_result",
                    "step_title": f"已获得{tool_display}结果",
                    "step_detail": f"执行结果: {res_summary}"
                }
                new_traces.append(trace_res_item)
                yield {"type": "trace", "data": trace_res_item}

                # 构建 tool 消息返回给大模型
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": json.dumps(tool_res["result"], ensure_ascii=False)
                })

        # 6. 将检索来源结果 yield 给前端页面展示
        if retrieved_rag_sources:
            yield {"type": "sources", "data": retrieved_rag_sources}

        # 7. 模型流式生成最终汇总回答
        step_idx += 1
        trace_final_item = {
            "step_index": step_idx,
            "step_type": "generate",
            "step_title": "正在生成综合回答",
            "step_detail": "整合工具返回的数据及检索来源，输出最终的回答信息。"
        }
        new_traces.append(trace_final_item)
        yield {"type": "trace", "data": trace_final_item}

        # 流式获取最终文本
        # 由于流式需要我们传递不带 tools 的对话给 chat_stream 或直接自己调用 stream
        full_response = ""
        try:
            logger.info("Agent 正在生成流式最终应答...")
            # 我们直接使用 client 构造 stream，传入包含工具交互历史的 messages 列表，不带 tools 即可让其专注于生成
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    text_delta = chunk.choices[0].delta.content
                    full_response += text_delta
                    yield {"type": "text", "data": text_delta}
        except Exception as se:
            logger.error(f"Agent 流式生成回答失败: {se}")
            # 如果流式报错，回退非流式
            if response_message.content:
                full_response = response_message.content
                yield {"type": "text", "data": full_response}
            else:
                yield {"type": "error", "data": f"最终生成回答时异常: {str(se)}"}
                return

        response_time_ms = int((time.time() - start_time) * 1000)

        # 8. 保存消息入库与轨迹关联
        # 保存助手回答消息
        assistant_msg_id = sqlite_repository.save_message(
            session_id=session_id,
            role="assistant",
            content=full_response,
            intent=intent,
            intent_name=intent_name,
            intent_confidence=intent_res["confidence"],
            intent_reason=intent_res["reason"],
            rewritten_query=user_content,
            has_source=1 if retrieved_rag_sources else 0,
            response_time_ms=response_time_ms,
            agent_mode=1,
            tool_used=1 if tool_used_count > 0 else 0
        )
        
        # 将 RAG 来源关联存入 SQLite
        if retrieved_rag_sources:
            sqlite_repository.save_message_sources(assistant_msg_id, retrieved_rag_sources)

        # 9. 批量将轨迹数据持久化入库，并关联 assistant_msg_id
        for trace in new_traces:
            record_agent_trace(
                session_id=session_id,
                message_id=assistant_msg_id,
                step_index=trace["step_index"],
                step_type=trace["step_type"],
                step_title=trace["step_title"],
                step_detail=trace["step_detail"]
            )
            
        # 并把 tool_logs 表里未关联的本次调用的 message_id 进行更新
        # 为了简单，我们在 tool_registry 里写入时没有 message_id，现在我们直接在 SQLite 中关联更新！
        # 我们可以根据 session_id 且 created_at 接近的来进行更新
        try:
            with sqlite_repository.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tool_logs 
                    SET message_id = ? 
                    WHERE session_id = ? AND (message_id IS NULL OR message_id = "")
                ''', (assistant_msg_id, session_id))
                conn.commit()
        except Exception as ule:
            logger.error(f"联表更新工具日志的消息ID失败: {ule}")

        # 10. 进行回答质量评估并入库
        try:
            eval_res = self.quality_service.evaluate_and_save(
                message_id=assistant_msg_id,
                session_id=session_id,
                query=user_content,
                answer=full_response,
                sources=retrieved_rag_sources,
                tool_logs=executed_tool_logs
            )
            yield {"type": "quality", "data": eval_res}
        except Exception as qe:
            logger.error(f"进行最终质量评估失败: {qe}")
