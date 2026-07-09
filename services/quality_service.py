import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from config import settings
from utils.logger import logger
from repositories import sqlite_repository

class QualityService:
    def __init__(self):
        """
        初始化回答质量评估服务。
        """
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.model = settings.CHAT_MODEL
        self._client = None
        
        # 是否启用大模型评估开关，默认开启
        self.enable_llm_eval = True

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

    def evaluate_by_rules(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        tool_logs: List[Dict[str, Any]],
        feedback_rating: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        基于预定义规则评估问答质量。
        规则：
        - 基础分：3 分。
        - 有来源：+1。
        - 工具调用成功：+1。
        - 回答包含“当前知识库未检索到相关依据”且确实无来源：+1。
        - 无来源但回答了政策类（招生/学务）问题：-2。
        - 用户反馈点踩 (dislike)：-2。
        - 工具调用失败：-1。
        - 限制分数范围为 1 ~ 5 分。
        - 低于 3 分或无来源且涉及政策类问题时标记为低质量。
        """
        score = 3
        issues = []
        suggestions = []
        
        # 1. 来源检查
        has_source = len(sources) > 0
        if has_source:
            score += 1
        
        # 2. 工具调用状态
        has_tool = len(tool_logs) > 0
        tool_success = True
        if has_tool:
            any_fail = any(not t.get("success", True) for t in tool_logs)
            if any_fail:
                score -= 1
                tool_success = False
                issues.append("部分工具调用失败")
                suggestions.append("检查天气或校历等外部工具接口是否正常")
            else:
                score += 1
                
        # 3. 兜底未检索匹配判定
        no_evidence_keywords = ["当前知识库未检索到相关依据", "未检索到相关依据", "没有检索到相关"]
        has_no_evidence_reply = any(kw in answer for kw in no_evidence_keywords)
        if has_no_evidence_reply and not has_source:
            score += 1
            
        # 4. 意图与政策性风险识别
        # 判断提问是否是招生或学务类政策提问
        policy_keywords = ["招生", "录取", "分数线", "专业", "报考", "志愿", "新生", "报到", "选课", "考试", "成绩", "学籍", "奖学金", "助学金", "毕业", "绩点", "学费", "缴费"]
        is_policy = any(kw in query for kw in policy_keywords)
        
        if not has_source and is_policy and not has_no_evidence_reply:
            score -= 2
            issues.append("未查阅知识库却直接回答政策类提问，存在编造风险")
            suggestions.append("建议导入相关招生/学务文档，或在未匹配时返回兜底提示信息")

        # 5. 反馈情况
        if feedback_rating == "dislike":
            score -= 2
            issues.append("用户提交了不满意反馈")
            suggestions.append("用户反馈回答不准确，请人工核对并修正知识库条目")

        # 限制在 1 - 5 分
        score = max(1, min(5, score))
        
        # 判定是否低质量回答
        is_low_quality = False
        if score < 3:
            is_low_quality = True
        elif not has_source and is_policy and not has_no_evidence_reply:
            is_low_quality = True
            
        if is_low_quality:
            if not issues:
                issues.append("综合得分较低")
            if not suggestions:
                suggestions.append("建议补充关联知识库文档以提供更准确的依据")

        suggestion_text = "、".join(suggestions) if suggestions else "回答依据较充分"
        
        return {
            "score": score,
            "is_low_quality": is_low_quality,
            "issues": issues,
            "suggestion": suggestion_text
        }

    def evaluate_by_llm(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        tool_logs: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        调用大模型对客服回答进行多维度质量审查，仅返回规范 JSON。
        """
        system_prompt = """你是一个专业的客服问答质量评估专家。你的任务是评估系统给出的客服回答（answer）是否高质量。
输入包含：用户提问、检索来源切片、工具调用记录以及实际客服回答。

【评估标准】
1. score (评分，1-5分):
   - 5分：完全基于检索来源或成功调用的工具作答，没有编造，排版优美，回答准确。
   - 4分：依据充分，解答了用户的大部分核心问题，只有极细微的不完美。
   - 3分：基本解答了问题，但无来源或证据不充实，或者是闲聊。
   - 2分：没有解答用户问题，或者未找到来源但却自信地编造了政策性的答案（如电话、日期等）。
   - 1分：回答内容有严重的事实性错误或无脑胡说八道。
2. is_low_quality (是否为低质量回答):
   - 得分低于3分，或者没有引用来源但回答了招生、教务等敏感的政策性问题。
3. issues (问题列表，数组形式):
   - 说明存在的问题，如“无知识库来源”、“可能编造政策时间”、“回答文不对题”、“工具调用失败”等。如果一切良好，输出空数组。
4. suggestion (优化建议):
   - 说明具体的改进方向，如“应补充相关学院的报到时间文档”、“添加退学政策的规章”等。如果优秀，输出“无需人工优化”。

【约束条件】
必须只返回符合 JSON 规范的字符串，且包含 keys: "score", "is_low_quality", "issues", "suggestion"。
不要包含任何 markdown 包装，不要带前缀或解释。
"""

        sources_str = "\n".join([f"- {s['file_name']}: {s['source_text']}" for s in sources]) if sources else "无检索来源"
        tools_str = "\n".join([f"- {t['name']}(成功={t['success']}): {t['result']}" for t in tool_logs]) if tool_logs else "无工具调用"
        
        user_content = f"""【用户提问】\n{query}
【知识库来源】\n{sources_str}
【工具调用】\n{tools_str}
【客服回答】\n{answer}

请给出质量评估 JSON："""

        try:
            logger.info("开始调用大模型对回答质量进行评估...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1
            )
            raw_content = response.choices[0].message.content.strip()
            
            # 清理可能包含的 Markdown 标记
            if raw_content.startswith("```"):
                lines = raw_content.splitlines()
                clean_lines = [l for l in lines if not l.strip().startswith("```")]
                raw_content = "\n".join(clean_lines).strip()
                
            eval_res = json.loads(raw_content)
            
            # 基础字段校验与纠正
            eval_res["score"] = max(1, min(5, int(eval_res.get("score", 3))))
            eval_res["is_low_quality"] = bool(eval_res.get("is_low_quality", eval_res["score"] < 3))
            
            issues = eval_res.get("issues", [])
            if isinstance(issues, str):
                issues = [issues]
            eval_res["issues"] = issues
            
            if "suggestion" not in eval_res:
                eval_res["suggestion"] = "无"
                
            logger.info(f"大模型评估完成，得分: {eval_res['score']}, 低质量: {eval_res['is_low_quality']}")
            return eval_res
        except Exception as e:
            logger.error(f"大模型评估失败或解析异常: {e}，将回退到规则评估。")
            return None

    def evaluate_and_save(
        self,
        message_id: str,
        session_id: str,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        tool_logs: List[Dict[str, Any]],
        feedback_rating: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        对一次问答执行评估，并将结果写入 SQLite 数据库中的 quality_evaluations 表，同时同步更新 messages 里的字段。
        """
        eval_res = None
        evaluator = "rules"
        
        # 1. 尝试大模型评估
        if self.enable_llm_eval and self.api_key:
            eval_res = self.evaluate_by_llm(query, answer, sources, tool_logs)
            if eval_res:
                evaluator = "llm"
                
        # 2. 大模型失败或关闭时，使用规则评估
        if not eval_res:
            eval_res = self.evaluate_by_rules(query, answer, sources, tool_logs, feedback_rating)
            evaluator = "rules"
            
        # 3. 将结果保存到 SQLite
        try:
            issues_str = json.dumps(eval_res["issues"], ensure_ascii=False)
            sqlite_repository.save_quality_evaluation(
                message_id=message_id,
                session_id=session_id,
                score=eval_res["score"],
                is_low_quality=1 if eval_res["is_low_quality"] else 0,
                issues=issues_str,
                suggestion=eval_res["suggestion"],
                evaluator=evaluator
            )
            logger.info(f"质量评估结果成功入库 (评估器: {evaluator})。评分: {eval_res['score']}")
        except Exception as dbe:
            logger.error(f"将质量评估保存到数据库异常: {dbe}")
            
        return eval_res

    def reevaluate_on_feedback(self, message_id: str, feedback_rating: str) -> Optional[Dict[str, Any]]:
        """
        当用户进行点赞点踩反馈时，触发重新评估，更新质量评估记录和消息分数。
        """
        try:
            # 1. 从数据库读取问答明细
            with sqlite_repository.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        m.content as answer,
                        m.session_id,
                        m.intent_name,
                        m_usr.content as query
                    FROM messages m
                    LEFT JOIN messages m_usr ON m_usr.rowid = (
                        SELECT MAX(rowid) FROM messages 
                        WHERE session_id = m.session_id 
                          AND role = 'user' 
                          AND rowid < m.rowid
                    )
                    WHERE m.message_id = ?
                """, (message_id,))
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"未能查询到 message_id = {message_id} 的记录，跳过反馈质量重评。")
                    return None
                
                row_dict = dict(row)
                query = row_dict["query"] or ""
                answer = row_dict["answer"] or ""
                session_id = row_dict["session_id"]
                
                # 2. 读取 RAG 来源和工具日志
                sources = sqlite_repository.get_message_sources(message_id)
                
                # 获取本次 session 下的工具日志
                cursor.execute("SELECT * FROM tool_logs WHERE message_id = ?", (message_id,))
                tool_rows = cursor.fetchall()
                tool_logs = [dict(tr) for tr in tool_rows]
                
            # 3. 运行规则评估（带上反馈信息进行计算）
            # 点踩直接减2分，可能会导致本来高分的变为低质量，非常符合实际情况！
            eval_res = self.evaluate_by_rules(query, answer, sources, tool_logs, feedback_rating)
            
            # 4. 更新到数据库中
            issues_str = json.dumps(eval_res["issues"], ensure_ascii=False)
            
            # 检查原评估是否存在，存在则更新，不存在则插入
            with sqlite_repository.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT evaluation_id FROM quality_evaluations WHERE message_id = ?", (message_id,))
                eval_row = cursor.fetchone()
                
                if eval_row:
                    cursor.execute("""
                        UPDATE quality_evaluations 
                        SET score = ?, is_low_quality = ?, issues = ?, suggestion = ?, evaluator = ?, created_at = datetime('now', 'localtime')
                        WHERE message_id = ?
                    """, (eval_res["score"], 1 if eval_res["is_low_quality"] else 0, issues_str, eval_res["suggestion"], "rules_feedback", message_id))
                    
                    # 更新 messages
                    cursor.execute("""
                        UPDATE messages 
                        SET quality_score = ?, is_low_quality = ? 
                        WHERE message_id = ?
                    """, (eval_res["score"], 1 if eval_res["is_low_quality"] else 0, message_id))
                    conn.commit()
                else:
                    self.evaluate_and_save(message_id, session_id, query, answer, sources, tool_logs, feedback_rating)
                    
            logger.info(f"成功因为用户反馈 {feedback_rating} 重新计算回答 {message_id} 的质量分为 {eval_res['score']}")
            return eval_res
        except Exception as e:
            logger.error(f"因为反馈重评质量时异常: {e}")
            return None
