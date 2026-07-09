import os
import unittest
from config import settings

# 强行覆盖数据库路径为测试专属路径
settings.SQLITE_PATH = "data/test_campus_service.db"

from repositories import sqlite_repository

class TestSQLiteRepository(unittest.TestCase):
    def setUp(self):
        """
        每次测试前的准备工作：重新初始化库表。
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(settings.SQLITE_PATH), exist_ok=True)
        # 用 DROP TABLE 代替删除文件，彻底避免 Windows 文件锁定问题
        try:
            with sqlite_repository.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS message_sources")
                cursor.execute("DROP TABLE IF EXISTS messages")
                cursor.execute("DROP TABLE IF EXISTS chat_sessions")
                cursor.execute("DROP TABLE IF EXISTS documents")
                conn.commit()
        except Exception:
            pass
        sqlite_repository.init_db()

    def tearDown(self):
        """
        每次测试后的清理工作：删除临时测试数据库文件。
        """
        if os.path.exists(settings.SQLITE_PATH):
            try:
                os.remove(settings.SQLITE_PATH)
            except PermissionError:
                pass

    def test_document_operations(self):
        # 1. 保存文档
        doc_id = "test-doc-123"
        success = sqlite_repository.save_document(
            doc_id=doc_id,
            file_name="测试文件.pdf",
            file_path="/path/to/测试文件.pdf",
            file_type="pdf",
            file_hash="hash-123456",
            status="processing"
        )
        self.assertTrue(success)

        # 2. 通过哈希查询
        doc = sqlite_repository.get_document_by_hash("hash-123456")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["doc_id"], doc_id)
        self.assertEqual(doc["status"], "processing")

        # 2.5 通过 id 查询 (get_document)
        doc_by_id = sqlite_repository.get_document(doc_id)
        self.assertIsNotNone(doc_by_id)
        self.assertEqual(doc_by_id["file_hash"], "hash-123456")

        # 3. 更新状态
        update_success = sqlite_repository.update_document_status(
            doc_id=doc_id,
            status="completed",
            chunk_count=10
        )
        self.assertTrue(update_success)

        doc_updated = sqlite_repository.get_document_by_hash("hash-123456")
        self.assertEqual(doc_updated["status"], "completed")
        self.assertEqual(doc_updated["chunk_count"], 10)

        # 4. 列出所有文档
        docs = sqlite_repository.list_documents()
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["file_name"], "测试文件.pdf")

        # 5. 删除文档
        del_success = sqlite_repository.delete_document_record(doc_id)
        self.assertTrue(del_success)
        self.assertIsNone(sqlite_repository.get_document_by_hash("hash-123456"))

    def test_chat_and_message_operations(self):
        # 1. 创建会话
        session_id = sqlite_repository.create_chat_session(title="新建咨询会话")
        self.assertIsNotNone(session_id)

        # 2. 会话列表
        sessions = sqlite_repository.list_chat_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["title"], "新建咨询会话")
        self.assertEqual(sessions[0]["message_count"], 0)

        # 3. 更新标题
        sqlite_repository.update_session_title(session_id, "关于奖学金的追问")
        sessions = sqlite_repository.list_chat_sessions()
        self.assertEqual(sessions[0]["title"], "关于奖学金的追问")

        # 4. 保存消息
        user_msg_id = sqlite_repository.save_message(session_id, role="user", content="奖学金怎么申请？")
        self.assertIsNotNone(user_msg_id)

        assistant_msg_id = sqlite_repository.save_message(session_id, role="assistant", content="需要满足以下条件...")
        self.assertIsNotNone(assistant_msg_id)

        # 5. 查询消息
        msgs = sqlite_repository.get_chat_messages(session_id)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertEqual(msgs[1]["role"], "assistant")

        # 限制条数查询
        limit_msgs = sqlite_repository.get_chat_messages(session_id, limit=1)
        self.assertEqual(len(limit_msgs), 1)
        self.assertEqual(limit_msgs[0]["role"], "assistant")  # 最新的消息

        # 6. 保存和查询消息来源
        sources = [
            {
                "doc_id": "doc-999",
                "chunk_id": "chunk-1",
                "file_name": "学生手册.pdf",
                "page_number": 12,
                "chunk_index": 5,
                "source_text": "国家奖学金申请条件为学习成绩优异...",
                "similarity_distance": 0.15
            }
        ]
        src_success = sqlite_repository.save_message_sources(assistant_msg_id, sources)
        self.assertTrue(src_success)

        retrieved_sources = sqlite_repository.get_message_sources(assistant_msg_id)
        self.assertEqual(len(retrieved_sources), 1)
        self.assertEqual(retrieved_sources[0]["doc_id"], "doc-999")
        self.assertEqual(retrieved_sources[0]["page_number"], 12)
        self.assertEqual(retrieved_sources[0]["similarity_distance"], 0.15)

        # 7. 级联删除会话
        del_sess_success = sqlite_repository.delete_chat_session(session_id)
        self.assertTrue(del_sess_success)
        # 确认会话、消息及来源全部被级联删除
        self.assertEqual(len(sqlite_repository.list_chat_sessions()), 0)
        self.assertEqual(len(sqlite_repository.get_chat_messages(session_id)), 0)
        self.assertEqual(len(sqlite_repository.get_message_sources(assistant_msg_id)), 0)

if __name__ == '__main__':
    unittest.main()
