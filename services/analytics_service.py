import datetime
import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional
from repositories import sqlite_repository
from utils.logger import logger

class AnalyticsService:
    def __init__(self):
        """
        初始化统计分析服务。
        """
        pass

    def get_summary_metrics(self) -> Dict[str, Any]:
        """
        查询关键指标：总问答量、今日问答量、总会话数、知识库文档数、满意度、平均质量分、低质量回答数、工具调用数。
        数据全部实时从 SQLite 查询。
        """
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        metrics = {
            "total_qa_count": 0,
            "today_qa_count": 0,
            "total_session_count": 0,
            "total_doc_count": 0,
            "satisfaction_rate": None,  # 为 None 代表暂无反馈
            "average_quality_score": None,
            "low_quality_count": 0,
            "total_tool_calls": 0
        }

        try:
            with sqlite_repository.get_connection() as conn:
                cursor = conn.cursor()

                # 1. 总问答量 (以 assistant 的消息数为准)
                cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'assistant'")
                metrics["total_qa_count"] = cursor.fetchone()[0]

                # 2. 今日问答量
                cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'assistant' AND created_at LIKE ?", (f"{today_str}%",))
                metrics["today_qa_count"] = cursor.fetchone()[0]

                # 3. 总会话数
                cursor.execute("SELECT COUNT(*) FROM chat_sessions")
                metrics["total_session_count"] = cursor.fetchone()[0]

                # 4. 知识库文档数 (排除已删除的)
                cursor.execute("SELECT COUNT(*) FROM documents WHERE status = 'completed' AND (deleted_at IS NULL OR deleted_at = '')")
                metrics["total_doc_count"] = cursor.fetchone()[0]

                # 5. 满意度 (点赞数 / (点赞数 + 点踩数))
                cursor.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating")
                feedback_counts = dict(cursor.fetchall())
                likes = feedback_counts.get("like", 0)
                dislikes = feedback_counts.get("dislike", 0)
                total_fb = likes + dislikes
                if total_fb > 0:
                    metrics["satisfaction_rate"] = likes / total_fb
                else:
                    metrics["satisfaction_rate"] = None

                # 6. 平均质量分
                cursor.execute("SELECT AVG(score) FROM quality_evaluations")
                avg_val = cursor.fetchone()[0]
                metrics["average_quality_score"] = round(avg_val, 2) if avg_val is not None else None

                # 7. 低质量回答数
                cursor.execute("SELECT COUNT(*) FROM quality_evaluations WHERE is_low_quality = 1")
                metrics["low_quality_count"] = cursor.fetchone()[0]

                # 8. 工具总调用数
                cursor.execute("SELECT COUNT(*) FROM tool_logs")
                metrics["total_tool_calls"] = cursor.fetchone()[0]

        except sqlite3.Error as e:
            logger.error(f"查询看板关键指标异常: {e}")

        return metrics

    def get_low_quality_messages_detail(self, limit: int = 10) -> pd.DataFrame:
        """
        获取最近低质量回答的问题和改进建议明细，供看板展示。
        """
        try:
            with sqlite_repository.get_connection() as conn:
                sql = """
                    SELECT 
                        q.created_at as time,
                        m_usr.content as user_question,
                        m_ast.content as assistant_answer,
                        q.score as score,
                        q.issues as issues,
                        q.suggestion as suggestion
                    FROM quality_evaluations q
                    JOIN messages m_ast ON q.message_id = m_ast.message_id
                    LEFT JOIN messages m_usr ON m_usr.rowid = (
                        SELECT MAX(rowid) FROM messages 
                        WHERE session_id = m_ast.session_id 
                          AND role = 'user' 
                          AND rowid < m_ast.rowid
                    )
                    WHERE q.is_low_quality = 1
                    ORDER BY q.created_at DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(sql, conn, params=(limit,))
                if df.empty:
                    return pd.DataFrame(columns=["time", "user_question", "assistant_answer", "score", "issues", "suggestion"])
                return df
        except Exception as e:
            logger.error(f"查询低质量问题明细异常: {e}")
            return pd.DataFrame(columns=["time", "user_question", "assistant_answer", "score", "issues", "suggestion"])

    def get_daily_trend(self, days: int = 30) -> pd.DataFrame:
        """
        统计最近 days 天内的每日问答趋势。
        """
        try:
            with sqlite_repository.get_connection() as conn:
                # 统计每日 assistant 消息数作为问答量
                sql = """
                    SELECT substr(created_at, 1, 10) as date, COUNT(*) as qa_count 
                    FROM messages 
                    WHERE role = 'assistant'
                    GROUP BY date 
                    ORDER BY date ASC
                """
                df = pd.read_sql_query(sql, conn)
                
                # 如果没有数据，返回包含标准列的空 DataFrame
                if df.empty:
                    return pd.DataFrame(columns=["date", "qa_count"])
                
                # 可选：可以用 pandas 对日期进行补齐，保证图表美观
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date")
                
                # 生成完整日期范围
                end_date = datetime.datetime.now()
                start_date = end_date - datetime.timedelta(days=days-1)
                idx = pd.date_range(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                
                # 重新索引，缺失值填为 0
                df = df.reindex(idx, fill_value=0)
                df = df.reset_index().rename(columns={"index": "date"})
                df["date"] = df["date"].dt.strftime('%Y-%m-%d')
                return df
        except Exception as e:
            logger.error(f"查询每日问答趋势异常: {e}")
            return pd.DataFrame(columns=["date", "qa_count"])

    def get_intent_distribution(self) -> pd.DataFrame:
        """
        获取意图类别的分布比例。
        """
        try:
            with sqlite_repository.get_connection() as conn:
                sql = """
                    SELECT intent_name, COUNT(*) as count 
                    FROM messages 
                    WHERE role = 'assistant' AND intent_name IS NOT NULL
                    GROUP BY intent_name
                    ORDER BY count DESC
                """
                df = pd.read_sql_query(sql, conn)
                if df.empty:
                    return pd.DataFrame(columns=["intent_name", "count"])
                return df
        except Exception as e:
            logger.error(f"查询意图分布异常: {e}")
            return pd.DataFrame(columns=["intent_name", "count"])

    def get_top_questions(self, limit: int = 10) -> pd.DataFrame:
        """
        统计热门问题 Top 10。
        """
        try:
            with sqlite_repository.get_connection() as conn:
                sql = """
                    SELECT content as question, COUNT(*) as count 
                    FROM messages 
                    WHERE role = 'user'
                    GROUP BY content 
                    ORDER BY count DESC 
                    LIMIT ?
                """
                df = pd.read_sql_query(sql, conn, params=(limit,))
                if df.empty:
                    return pd.DataFrame(columns=["question", "count"])
                return df
        except Exception as e:
            logger.error(f"查询热门问题异常: {e}")
            return pd.DataFrame(columns=["question", "count"])

    def get_low_satisfaction_messages(self) -> pd.DataFrame:
        """
        获取所有被点踩（dislike）的问答对明细。
        返回 DataFrame 列：feedback_time, comment, user_question, assistant_answer, intent
        """
        try:
            with sqlite_repository.get_connection() as conn:
                sql = """
                    SELECT 
                        f.created_at as feedback_time,
                        f.comment as comment,
                        m_ast.content as assistant_answer,
                        m_ast.intent_name as intent,
                        m_usr.content as user_question
                    FROM feedback f
                    JOIN messages m_ast ON f.message_id = m_ast.message_id
                    LEFT JOIN messages m_usr ON m_usr.rowid = (
                        SELECT MAX(rowid) FROM messages 
                        WHERE session_id = m_ast.session_id 
                          AND role = 'user' 
                          AND rowid < m_ast.rowid
                    )
                    WHERE f.rating = 'dislike'
                    ORDER BY f.created_at DESC
                """
                df = pd.read_sql_query(sql, conn)
                if df.empty:
                    return pd.DataFrame(columns=["feedback_time", "comment", "user_question", "assistant_answer", "intent"])
                return df
        except Exception as e:
            logger.error(f"查询低满意度问答异常: {e}")
            return pd.DataFrame(columns=["feedback_time", "comment", "user_question", "assistant_answer", "intent"])

    def get_session_logs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        intent: Optional[str] = None,
        has_source: Optional[int] = None,
        is_disliked: Optional[bool] = None,
        search_keyword: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        多条件筛选会话日志明细，返回问答对列表。
        """
        query_sql = """
            SELECT 
                m_ast.message_id,
                m_ast.session_id,
                m_ast.created_at as time,
                m_ast.content as assistant_answer,
                m_ast.intent,
                m_ast.intent_name,
                m_ast.intent_confidence,
                m_ast.rewritten_query,
                m_ast.has_source,
                m_ast.response_time_ms,
                m_usr.content as user_question,
                f.rating as feedback_rating,
                f.comment as feedback_comment
            FROM messages m_ast
            LEFT JOIN messages m_usr ON m_usr.rowid = (
                SELECT MAX(rowid) FROM messages 
                WHERE session_id = m_ast.session_id 
                  AND role = 'user' 
                  AND rowid < m_ast.rowid
            )
            LEFT JOIN feedback f ON m_ast.message_id = f.message_id
            WHERE m_ast.role = 'assistant'
        """

        conditions = []
        params = {}

        if start_date:
            conditions.append("m_ast.created_at >= :start_date")
            params["start_date"] = f"{start_date} 00:00:00"
        if end_date:
            conditions.append("m_ast.created_at <= :end_date")
            params["end_date"] = f"{end_date} 23:59:59"
        if intent:
            conditions.append("m_ast.intent = :intent")
            params["intent"] = intent
        if has_source is not None:
            conditions.append("m_ast.has_source = :has_source")
            params["has_source"] = has_source
        if is_disliked:
            conditions.append("f.rating = 'dislike'")

        if search_keyword:
            # 模糊匹配用户问题或助手回答
            conditions.append("(m_ast.content LIKE :search_keyword OR m_usr.content LIKE :search_keyword)")
            params["search_keyword"] = f"%{search_keyword}%"

        if conditions:
            query_sql += " AND " + " AND ".join(conditions)

        query_sql += " ORDER BY m_ast.created_at DESC"

        try:
            with sqlite_repository.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query_sql, params)
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"多条件查询会话日志异常: {e}")
            return []

    def get_unanswered_questions_top(self, limit: int = 10) -> pd.DataFrame:
        """
        获取知识库未命中问题 Top N（has_source=0 的用户提问频次排名）。
        """
        try:
            with sqlite_repository.get_connection() as conn:
                sql = """
                    SELECT m_usr.content as question, COUNT(*) as count
                    FROM messages m_ast
                    LEFT JOIN messages m_usr ON m_usr.rowid = (
                        SELECT MAX(rowid) FROM messages
                        WHERE session_id = m_ast.session_id
                          AND role = 'user'
                          AND rowid < m_ast.rowid
                    )
                    WHERE m_ast.role = 'assistant'
                      AND (m_ast.has_source = 0 OR m_ast.has_source IS NULL)
                      AND m_usr.content IS NOT NULL
                    GROUP BY m_usr.content
                    ORDER BY count DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(sql, conn, params=(limit,))
                if df.empty:
                    return pd.DataFrame(columns=["question", "count"])
                return df
        except Exception as e:
            logger.error(f"查询未命中问题 Top N 异常: {e}")
            return pd.DataFrame(columns=["question", "count"])

    def get_no_source_messages(self, limit: int = 20) -> list:
        """
        获取最近的无来源回答消息列表。
        """
        try:
            with sqlite_repository.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m_ast.message_id, m_ast.session_id, m_ast.created_at,
                           m_ast.content as assistant_answer,
                           m_usr.content as user_question
                    FROM messages m_ast
                    LEFT JOIN messages m_usr ON m_usr.rowid = (
                        SELECT MAX(rowid) FROM messages
                        WHERE session_id = m_ast.session_id
                          AND role = 'user'
                          AND rowid < m_ast.rowid
                    )
                    WHERE m_ast.role = 'assistant'
                      AND (m_ast.has_source = 0 OR m_ast.has_source IS NULL)
                    ORDER BY m_ast.created_at DESC
                    LIMIT ?
                """, (limit,))
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"查询无来源回答消息异常: {e}")
            return []

    def get_no_source_rate(self):
        """
        计算无来源回答的占比（百分比数值）。
        返回 float 或 None（无数据时）。
        """
        try:
            with sqlite_repository.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'assistant'")
                total = cursor.fetchone()[0]
                if total == 0:
                    return None
                cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'assistant' AND (has_source = 0 OR has_source IS NULL)")
                no_source = cursor.fetchone()[0]
                return (no_source / total) * 100
        except Exception as e:
            logger.error(f"计算无来源率异常: {e}")
            return None
