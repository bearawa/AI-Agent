import os
import unittest
from unittest.mock import MagicMock, patch
from config import settings

# 强行覆盖数据库路径为测试专属路径
settings.SQLITE_PATH = "data/test_campus_service_db_rag.db"

from repositories import sqlite_repository
from services.rag_service import RAGService

class TestRAGService(unittest.TestCase):
    def setUp(self):
        """
        测试前准备：初始化数据库。
        """
        os.makedirs(os.path.dirname(settings.SQLITE_PATH), exist_ok=True)
        # 用 DROP TABLE 彻底清空表
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
        
        # 实例化待测服务
        self.rag_service = RAGService()

    def tearDown(self):
        """
        测试后清理。
        """
        if os.path.exists(settings.SQLITE_PATH):
            try:
                os.remove(settings.SQLITE_PATH)
            except PermissionError:
                pass

    @patch("services.rag_service.DocumentService.parse_document")
    @patch("services.rag_service.EmbeddingService.get_embeddings_batch")
    @patch("services.rag_service.ChromaRepository.add_chunks")
    def test_import_document_success(self, mock_add_chunks, mock_get_embeddings, mock_parse_document):
        # 1. 模拟子服务行为
        mock_parse_document.return_value = [
            {"text": "切片内容1", "page_number": 1, "chunk_index": 0},
            {"text": "切片内容2", "page_number": 1, "chunk_index": 1}
        ]
        mock_get_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_add_chunks.return_value = True

        # 2. 执行导入
        file_name = "test_doc.pdf"
        file_bytes = b"pdf_fake_binary_content_12345"
        
        doc_id = self.rag_service.import_document(file_name, file_bytes)
        self.assertIsNotNone(doc_id)

        # 3. 校验数据库记录
        docs = sqlite_repository.list_documents()
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["doc_id"], doc_id)
        self.assertEqual(docs[0]["status"], "completed")
        self.assertEqual(docs[0]["chunk_count"], 2)

        # 清理刚才产生的物理文件（在 upload_dir 里保存了）
        local_path = docs[0]["file_path"]
        if os.path.exists(local_path):
            os.remove(local_path)

    @patch("services.rag_service.DocumentService.parse_document")
    def test_import_document_duplicate(self, mock_parse_document):
        # 1. 模拟在 SQLite 中已存在该哈希值的文件
        file_name = "existing_doc.txt"
        file_bytes = b"same_content"
        
        # 保存第一个
        self.rag_service.import_document(file_name, file_bytes)
        
        # 2. 再次导入相同内容，应当抛出 ValueError
        with self.assertRaises(ValueError) as context:
            self.rag_service.import_document("another_name.txt", file_bytes)
        
        self.assertIn("已在知识库中导入", str(context.exception))

        # 清理
        docs = sqlite_repository.list_documents()
        for doc in docs:
            if os.path.exists(doc["file_path"]):
                os.remove(doc["file_path"])

    @patch("services.rag_service.DocumentService.parse_document")
    @patch("services.rag_service.EmbeddingService.get_embeddings_batch")
    @patch("services.rag_service.ChromaRepository.add_chunks")
    @patch("services.rag_service.ChromaRepository.delete_by_doc_id")
    def test_import_document_failed_rollback(self, mock_delete_by_doc_id, mock_add_chunks, mock_get_embeddings, mock_parse_document):
        # 1. 模拟解析成功，但向量生成或者写入 Chroma 抛出异常
        mock_parse_document.return_value = [
            {"text": "切片内容", "page_number": None, "chunk_index": 0}
        ]
        mock_get_embeddings.side_effect = RuntimeError("百炼 Embedding 接口调用超时")

        # 2. 执行导入并捕获异常
        file_name = "error_doc.txt"
        file_bytes = b"some_error_content_data"

        with self.assertRaises(RuntimeError) as context:
            self.rag_service.import_document(file_name, file_bytes)
        
        self.assertIn("文档导入失败", str(context.exception))

        # 3. 校验 SQLite 状态应为 failed 并记录错误信息
        docs = sqlite_repository.list_documents()
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["status"], "failed")
        self.assertIn("百炼 Embedding 接口调用超时", docs[0]["error_message"])

        # 4. 确认触发了向量库清理函数
        mock_delete_by_doc_id.assert_called_once()

        # 清理
        if os.path.exists(docs[0]["file_path"]):
            os.remove(docs[0]["file_path"])

    @patch("services.rag_service.EmbeddingService.get_embedding")
    @patch("services.rag_service.ChromaRepository.query_similar_chunks")
    def test_search_relevant_chunks_filtering(self, mock_query_similar, mock_get_embedding):
        # 1. 模拟向量生成
        mock_get_embedding.return_value = [0.1, 0.2]
        
        # 2. 模拟向量检索返回 2 个切片，一个距离为 0.5 (符合)，一个为 0.95 (被过滤)
        mock_query_similar.return_value = [
            {
                "chunk_id": "chunk_1",
                "doc_id": "doc_123",
                "file_name": "手册.pdf",
                "page_number": 5,
                "chunk_index": 2,
                "source_text": "符合条件的文本段落",
                "similarity_distance": 0.5
            },
            {
                "chunk_id": "chunk_2",
                "doc_id": "doc_123",
                "file_name": "手册.pdf",
                "page_number": 6,
                "chunk_index": 3,
                "source_text": "相似度过低被过滤的文本段落",
                "similarity_distance": 0.95
            }
        ]

        # 3. 执行检索，设定相关性过滤阈值为 0.8 (在 settings.RAG_DISTANCE_THRESHOLD 设定)
        settings.RAG_DISTANCE_THRESHOLD = 0.8
        
        results = self.rag_service.search_relevant_chunks("怎么退学费？", top_k=5)

        # 4. 断言：应当只剩下 1 个结果
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "chunk_1")
        self.assertEqual(results[0]["source_text"], "符合条件的文本段落")

if __name__ == '__main__':
    unittest.main()
