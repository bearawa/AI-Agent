import sys
import os
import unittest
import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import settings
from repositories import sqlite_repository
from services.analytics_service import AnalyticsService

class TestAnalyticsService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 使用物理测试数据库以维持连接关闭后的表结构生命周期
        cls.orig_sqlite_path = settings.SQLITE_PATH
        cls.test_sqlite_path = "data/test_campus_service.db"
        settings.SQLITE_PATH = cls.test_sqlite_path
        # 初始化表结构
        sqlite_repository.init_db()

    @classmethod
    def tearDownClass(cls):
        settings.SQLITE_PATH = cls.orig_sqlite_path
        if os.path.exists(cls.test_sqlite_path):
            try:
                os.remove(cls.test_sqlite_path)
            except Exception:
                pass

    def setUp(self):
        self.analytics_service = AnalyticsService()
        self.clear_tables()
        self.insert_seed_data()

    def clear_tables(self):
        with sqlite_repository.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feedback")
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM chat_sessions")
            cursor.execute("DELETE FROM documents")
            conn.commit()

    def insert_seed_data(self):
        # 插入模拟的已入库文档
        sqlite_repository.save_document(
            doc_id="doc-1",
            file_name="招生指南.pdf",
            file_path="data/raw_documents/招生指南.pdf",
            file_type="pdf",
            file_hash="hash-1",
            status="completed",
            category="admission",
            category_name="招生"
        )
        sqlite_repository.update_document_status("doc-1", "completed", chunk_count=12)

        # 插入模拟的会话
        session_id = sqlite_repository.create_chat_session("测试会话 1", session_id="session-1")
        session_id2 = sqlite_repository.create_chat_session("测试会话 2", session_id="session-2")

        # 插入模拟的消息对 (问答对 1：招生分类，点赞)
        msg_id_usr1 = sqlite_repository.save_message(
            session_id="session-1",
            role="user",
            content="请问今年招生政策是怎样的？",
            message_id="msg-usr-1"
        )
        msg_id_ast1 = sqlite_repository.save_message(
            session_id="session-1",
            role="assistant",
            content="今年我校面向全国招收本科生...",
            message_id="msg-ast-1",
            intent="admission",
            intent_name="招生",
            intent_confidence=0.98,
            intent_reason="规则命中",
            rewritten_query="招生政策是什么",
            has_source=1,
            response_time_ms=120
        )
        sqlite_repository.save_or_update_feedback(
            message_id="msg-ast-1",
            session_id="session-1",
            rating="like",
            comment="非常有帮助！"
        )

        # 插入模拟的消息对 (问答对 2：学务分类，点踩)
        msg_id_usr2 = sqlite_repository.save_message(
            session_id="session-1",
            role="user",
            content="怎么查我的绩点？",
            message_id="msg-usr-2"
        )
        msg_id_ast2 = sqlite_repository.save_message(
            session_id="session-1",
            role="assistant",
            content="抱歉，知识库目前没有关于绩点查询的内容。",
            message_id="msg-ast-2",
            intent="academic",
            intent_name="学务",
            intent_confidence=0.95,
            intent_reason="规则命中",
            rewritten_query="如何查询绩点",
            has_source=0,
            response_time_ms=80
        )
        sqlite_repository.save_or_update_feedback(
            message_id="msg-ast-2",
            session_id="session-1",
            rating="dislike",
            comment="内容不准确"
        )

        # 插入问答对 3：重复的问题以测试 TopQuestions 统计
        sqlite_repository.save_message(
            session_id="session-2",
            role="user",
            content="请问今年招生政策是怎样的？",
            message_id="msg-usr-3"
        )
        sqlite_repository.save_message(
            session_id="session-2",
            role="assistant",
            content="您好，请参考招生指南...",
            message_id="msg-ast-3",
            intent="admission",
            intent_name="招生",
            intent_confidence=0.92
        )

    def test_get_summary_metrics(self):
        metrics = self.analytics_service.get_summary_metrics()
        self.assertEqual(metrics["total_qa_count"], 3)  # 3 条 assistant 消息
        self.assertEqual(metrics["total_session_count"], 2)  # 2 个会话
        self.assertEqual(metrics["total_doc_count"], 1)  # 1 个完成文档
        # 1 赞 1 踩，满意度为 50.0%
        self.assertEqual(metrics["satisfaction_rate"], 0.5)

    def test_get_daily_trend(self):
        df = self.analytics_service.get_daily_trend(days=7)
        self.assertEqual(len(df), 7)
        self.assertIn("date", df.columns)
        self.assertIn("qa_count", df.columns)
        # 最近一天的问答量应为 3 条（因为种子数据创建在当前时间）
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        today_row = df[df["date"] == today_str]
        self.assertFalse(today_row.empty)
        self.assertEqual(today_row.iloc[0]["qa_count"], 3)

    def test_get_intent_distribution(self):
        df = self.analytics_service.get_intent_distribution()
        self.assertEqual(len(df), 2)  # 招生(2条)、学务(1条)
        self.assertEqual(df[df["intent_name"] == "招生"].iloc[0]["count"], 2)
        self.assertEqual(df[df["intent_name"] == "学务"].iloc[0]["count"], 1)

    def test_get_top_questions(self):
        df = self.analytics_service.get_top_questions(limit=5)
        self.assertEqual(len(df), 2)  # 两种不同问题
        self.assertEqual(df.iloc[0]["question"], "请问今年招生政策是怎样的？")
        self.assertEqual(df.iloc[0]["count"], 2)  # 提问了两次

    def test_get_low_satisfaction_messages(self):
        df = self.analytics_service.get_low_satisfaction_messages()
        self.assertEqual(len(df), 1)  # 只有一个 dislike
        self.assertEqual(df.iloc[0]["user_question"], "怎么查我的绩点？")
        self.assertEqual(df.iloc[0]["comment"], "内容不准确")

    def test_get_session_logs_no_filter(self):
        logs = self.analytics_service.get_session_logs()
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0]["user_question"], "请问今年招生政策是怎样的？")
        # 按照时间倒序，最新创建的消息排在前面

    def test_get_session_logs_with_filter(self):
        # 过滤点踩的
        logs = self.analytics_service.get_session_logs(is_disliked=True)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["intent"], "academic")

        # 过滤关键词
        logs2 = self.analytics_service.get_session_logs(search_keyword="政策")
        self.assertEqual(len(logs2), 2)
        
        # 过滤分类
        logs3 = self.analytics_service.get_session_logs(intent="academic")
        self.assertEqual(len(logs3), 1)
        self.assertEqual(logs3[0]["user_question"], "怎么查我的绩点？")

if __name__ == "__main__":
    unittest.main()
