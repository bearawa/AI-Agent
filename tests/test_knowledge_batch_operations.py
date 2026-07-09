# -*- coding: utf-8 -*-
"""
AIZS 知识库批量操作功能测试
覆盖：批量删除、失败记录清理、message_sources 清理、repository 层功能验证

所有涉及 ChromaDB、Embedding 的地方均使用 Mock，不依赖真实 API Key。
"""
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call

# ─── 初始化测试用 SQLite（使用内存数据库） ───────────────────────
import sqlite3
from config import settings

# 获取 SQLite 路径（用于测试隔离）
_ORIG_SQLITE_PATH = settings.SQLITE_PATH


def _create_test_db():
    """在内存中创建隔离的测试数据库，返回连接。"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_hash TEXT UNIQUE NOT NULL,
            uploaded_at TEXT NOT NULL,
            status TEXT NOT NULL,
            chunk_count INTEGER DEFAULT 0,
            category TEXT DEFAULT 'other',
            category_name TEXT DEFAULT '其他',
            deleted_at TEXT,
            error_message TEXT
        );
        CREATE TABLE IF NOT EXISTS message_sources (
            source_id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            doc_id TEXT NOT NULL,
            chunk_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            page_number INTEGER,
            chunk_index INTEGER NOT NULL,
            source_text TEXT NOT NULL,
            similarity_distance REAL NOT NULL
        );
    """)
    conn.commit()
    return conn


class TestKnowledgeBatchOperations(unittest.TestCase):
    """测试知识库批量操作功能：批量删除、失败记录清理、Repository 层函数。"""

    def setUp(self):
        """每个测试用例前：创建隔离的临时 SQLite 数据库并 patch repository。"""
        # 临时文件用于模拟 SQLite 路径
        self._tmp_dir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmp_dir, "test.db")
        
        # Patch settings.SQLITE_PATH 使用临时数据库
        self._settings_patch = patch.object(settings, "SQLITE_PATH", self._db_path)
        self._settings_patch.start()

        # 初始化表结构
        from repositories import sqlite_repository
        sqlite_repository.init_db()
        self.sqlite_repo = sqlite_repository

        # Mock ChromaRepository（避免连接真实 ChromaDB）
        self._chroma_patch = patch("services.knowledge_admin_service.ChromaRepository")
        mock_chroma_cls = self._chroma_patch.start()
        self.mock_chroma = MagicMock()
        self.mock_chroma.delete_by_doc_id.return_value = True
        mock_chroma_cls.return_value = self.mock_chroma

        # 实例化被测服务
        from services.knowledge_admin_service import KnowledgeAdminService
        self.admin_service = KnowledgeAdminService()

    def tearDown(self):
        """测试结束后清理 patches 和临时文件。"""
        self._settings_patch.stop()
        self._chroma_patch.stop()
        import shutil
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def _insert_doc(self, doc_id, file_name, status="completed", file_path=None):
        """辅助：向 documents 表插入测试数据。"""
        if file_path is None:
            file_path = f"/tmp/{file_name}"
        import datetime
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.sqlite_repo.save_document(
            doc_id=doc_id,
            file_name=file_name,
            file_path=file_path,
            file_type="pdf",
            file_hash=f"hash_{doc_id}",
            status=status,
            category="other",
            category_name="其他"
        )
        if status != "processing":
            self.sqlite_repo.update_document_status(doc_id, status, chunk_count=5)

    def _insert_message_source(self, source_id, message_id, doc_id):
        """辅助：向 message_sources 表插入测试引用记录。"""
        from repositories import sqlite_repository as repo
        import sqlite3
        with repo.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO message_sources
                   (source_id, message_id, doc_id, chunk_id, file_name, chunk_index, source_text, similarity_distance)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (source_id, message_id, doc_id, f"{doc_id}_chunk_0", "test.pdf", 0, "测试来源文本", 0.3)
            )
            conn.commit()

    # ─────────────────────────────────────────────────────────────
    # 1. get_document 和 get_document_by_hash 存在且行为正确
    # ─────────────────────────────────────────────────────────────
    def test_get_document_returns_correct_record(self):
        """get_document 能根据 doc_id 正确返回文档。"""
        self._insert_doc("doc001", "测试文件.pdf", status="completed")
        doc = self.sqlite_repo.get_document("doc001")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["doc_id"], "doc001")
        self.assertEqual(doc["file_name"], "测试文件.pdf")

    def test_get_document_returns_none_for_missing(self):
        """get_document 查询不存在的 doc_id 返回 None，不报错。"""
        doc = self.sqlite_repo.get_document("nonexistent_id")
        self.assertIsNone(doc)

    def test_get_document_by_hash_returns_correct_record(self):
        """get_document_by_hash 能根据文件哈希正确返回文档，用于重复上传判断。"""
        self._insert_doc("doc002", "招生手册.pdf", status="completed")
        doc = self.sqlite_repo.get_document_by_hash("hash_doc002")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["doc_id"], "doc002")

    def test_get_document_by_hash_returns_none_for_missing(self):
        """get_document_by_hash 查询不存在的哈希返回 None。"""
        doc = self.sqlite_repo.get_document_by_hash("nonexistent_hash_xyz")
        self.assertIsNone(doc)

    # ─────────────────────────────────────────────────────────────
    # 2. delete_message_sources_by_doc_id 清除脏引用
    # ─────────────────────────────────────────────────────────────
    def test_delete_message_sources_by_doc_id(self):
        """delete_message_sources_by_doc_id 能正确清理指定文档的引用记录。"""
        self._insert_doc("doc003", "测试.pdf", status="completed")
        self._insert_message_source("src001", "msg001", "doc003")
        self._insert_message_source("src002", "msg002", "doc003")

        # 验证插入成功
        from repositories import sqlite_repository as repo
        with repo.get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM message_sources WHERE doc_id=?", ("doc003",)
            ).fetchone()[0]
        self.assertEqual(count, 2)

        # 执行清理
        ok = self.sqlite_repo.delete_message_sources_by_doc_id("doc003")
        self.assertTrue(ok)

        # 验证已清空
        with repo.get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM message_sources WHERE doc_id=?", ("doc003",)
            ).fetchone()[0]
        self.assertEqual(count, 0)

    # ─────────────────────────────────────────────────────────────
    # 3. list_failed_documents 只返回失败状态记录
    # ─────────────────────────────────────────────────────────────
    def test_list_failed_documents_only_returns_failed(self):
        """list_failed_documents 只返回 failed/error 等状态的文档，不返回成功文档。"""
        self._insert_doc("doc_ok1", "成功文档1.pdf", status="completed")
        self._insert_doc("doc_ok2", "成功文档2.pdf", status="completed")
        self._insert_doc("doc_fail1", "失败文档1.pdf", status="failed")
        self._insert_doc("doc_fail2", "失败文档2.pdf", status="error")

        failed = self.sqlite_repo.list_failed_documents()
        failed_ids = {d["doc_id"] for d in failed}

        self.assertIn("doc_fail1", failed_ids)
        self.assertIn("doc_fail2", failed_ids)
        self.assertNotIn("doc_ok1", failed_ids)
        self.assertNotIn("doc_ok2", failed_ids)

    # ─────────────────────────────────────────────────────────────
    # 4. delete_documents_batch 批量删除多个文档
    # ─────────────────────────────────────────────────────────────
    def test_delete_documents_batch_success(self):
        """delete_documents_batch 能成功批量删除多个文档。"""
        self._insert_doc("batch001", "文件A.pdf", status="completed")
        self._insert_doc("batch002", "文件B.pdf", status="completed")
        self._insert_doc("batch003", "文件C.pdf", status="completed")

        result = self.admin_service.delete_documents_batch(["batch001", "batch002", "batch003"])

        self.assertEqual(result["total"], 3)
        self.assertEqual(result["deleted"], 3)
        self.assertEqual(result["failed"], 0)

        # 验证已从数据库删除
        for doc_id in ["batch001", "batch002", "batch003"]:
            doc = self.sqlite_repo.get_document(doc_id)
            self.assertIsNone(doc)

    def test_delete_documents_batch_one_failure_does_not_affect_others(self):
        """批量删除时，一个文档删除失败不影响其他文档继续处理。"""
        self._insert_doc("batchA", "文件A.pdf", status="completed")
        self._insert_doc("batchC", "文件C.pdf", status="completed")

        # batchB 不存在（模拟找不到文档的情况）
        result = self.admin_service.delete_documents_batch(["batchA", "nonexistent_B", "batchC"])

        self.assertEqual(result["total"], 3)
        self.assertEqual(result["deleted"], 2)
        self.assertEqual(result["failed"], 1)

        # batchA 和 batchC 应已删除
        self.assertIsNone(self.sqlite_repo.get_document("batchA"))
        self.assertIsNone(self.sqlite_repo.get_document("batchC"))

        # 失败项应记录在 items 中
        failed_items = [item for item in result["items"] if item["status"] == "failed"]
        self.assertEqual(len(failed_items), 1)
        self.assertEqual(failed_items[0]["doc_id"], "nonexistent_B")

    def test_delete_documents_batch_empty_list(self):
        """delete_documents_batch 传入空列表时安全返回。"""
        result = self.admin_service.delete_documents_batch([])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["deleted"], 0)
        self.assertEqual(result["failed"], 0)

    # ─────────────────────────────────────────────────────────────
    # 5. clear_failed_documents 只清理失败状态文档
    # ─────────────────────────────────────────────────────────────
    def test_clear_failed_documents_only_clears_failed(self):
        """clear_failed_documents 只清理失败文档，不影响成功文档。"""
        self._insert_doc("ok_doc", "成功文档.pdf", status="completed")
        self._insert_doc("fail_doc1", "失败文档1.pdf", status="failed")
        self._insert_doc("fail_doc2", "失败文档2.pdf", status="error")

        result = self.admin_service.clear_failed_documents()

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["cleared"], 2)
        self.assertEqual(result["failed"], 0)

        # 成功文档依然存在
        ok = self.sqlite_repo.get_document("ok_doc")
        self.assertIsNotNone(ok)

        # 失败文档已清理
        self.assertIsNone(self.sqlite_repo.get_document("fail_doc1"))
        self.assertIsNone(self.sqlite_repo.get_document("fail_doc2"))

    def test_clear_failed_documents_no_failed_records(self):
        """没有失败记录时，clear_failed_documents 安全返回空结果。"""
        self._insert_doc("ok_only", "成功文档.pdf", status="completed")
        result = self.admin_service.clear_failed_documents()
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["cleared"], 0)

    def test_clear_failed_does_not_delete_completed_documents(self):
        """clear_failed_documents 绝不删除 completed/success 状态文档。"""
        self._insert_doc("protected1", "保护文档1.pdf", status="completed")
        self._insert_doc("protected2", "保护文档2.pdf", status="completed")
        self._insert_doc("should_clear", "需清理文档.pdf", status="failed")

        self.admin_service.clear_failed_documents()

        self.assertIsNotNone(self.sqlite_repo.get_document("protected1"))
        self.assertIsNotNone(self.sqlite_repo.get_document("protected2"))
        self.assertIsNone(self.sqlite_repo.get_document("should_clear"))

    # ─────────────────────────────────────────────────────────────
    # 6. 批量导入报告统计正确
    # ─────────────────────────────────────────────────────────────
    def test_batch_import_report_statistics(self):
        """build_import_report 正确统计成功/跳过/失败数量。"""
        from services.batch_import_service import BatchImportService
        
        with patch("services.batch_import_service.RAGService"):
            service = BatchImportService()

        results = [
            {"status": "success", "chunk_count": 5, "file_name": "a.pdf"},
            {"status": "success", "chunk_count": 3, "file_name": "b.pdf"},
            {"status": "skipped", "chunk_count": 0, "file_name": "c.pdf"},
            {"status": "failed", "chunk_count": 0, "file_name": "d.pdf"},
        ]
        report = service.build_import_report(results)

        self.assertEqual(report["total_files"], 4)
        self.assertEqual(report["success_count"], 2)
        self.assertEqual(report["skipped_count"], 1)
        self.assertEqual(report["failed_count"], 1)
        self.assertEqual(report["total_chunks"], 8)

    # ─────────────────────────────────────────────────────────────
    # 7. ZIP 路径穿越文件被拒绝
    # ─────────────────────────────────────────────────────────────
    def test_zip_path_traversal_is_blocked(self):
        """ZIP 压缩包中含 ../ 路径穿越文件名时，应被拒绝或标为失败，不写入目标目录外。"""
        from services.batch_import_service import BatchImportService
        import zipfile
        import io as _io

        # 构造一个含路径穿越文件名的 ZIP
        buf = _io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            # 正常文件
            zf.writestr("normal.txt", "合规文本内容")
            # 尝试路径穿越
            zi = zipfile.ZipInfo("../../evil.txt")
            zf.writestr(zi, "恶意内容")
        zip_bytes = buf.getvalue()

        with patch("services.batch_import_service.RAGService") as mock_rag_cls:
            mock_rag = MagicMock()
            mock_rag.import_document.return_value = "mock_doc_id"
            mock_rag_cls.return_value = mock_rag
            
            with patch("repositories.sqlite_repository.get_document") as mock_get_doc:
                mock_get_doc.return_value = {"chunk_count": 1}
                
                service = BatchImportService()
                results = service.import_zip_file(zip_bytes, "other")

        # 路径穿越文件应该被标为 failed，不会成功入库
        traversal_results = [r for r in results if "evil" in r.get("file_name", "")]
        for r in traversal_results:
            self.assertNotEqual(r["status"], "success",
                                "路径穿越文件不应该成功导入")

    # ─────────────────────────────────────────────────────────────
    # 8. 不支持的文件类型被 skipped
    # ─────────────────────────────────────────────────────────────
    def test_unsupported_file_type_is_skipped(self):
        """上传不支持文件类型（如 .xlsx）时，状态应为 failed（拦截）。"""
        from services.batch_import_service import BatchImportService
        with patch("services.batch_import_service.RAGService"):
            service = BatchImportService()
        
        result = service.import_single_file(b"fake content", "test.xlsx", "other")
        self.assertNotEqual(result["status"], "success",
                            "不支持的文件类型不应该成功导入")
        self.assertIsNotNone(result["error_message"])

    # ─────────────────────────────────────────────────────────────
    # 9. 不会删除 demo_documents 目录
    # ─────────────────────────────────────────────────────────────
    def test_clear_failed_does_not_delete_demo_documents_files(self):
        """clear_failed_documents 不应删除 demo_documents 目录中的原始文件。"""
        demo_dir = str(settings.BASE_DIR / "demo_documents")
        fake_demo_file = os.path.join(demo_dir, "fake_demo.txt")
        
        # 插入一个指向 demo_documents 目录的"失败"文档记录
        self._insert_doc("demo_fail", "fake_demo.txt", status="failed",
                         file_path=fake_demo_file)
        
        # 执行清理（不应删除 demo_documents 中的文件）
        with patch("os.remove") as mock_remove:
            self.admin_service.clear_failed_documents()
            # 确认 os.remove 没有被调用于 demo_dir 下的文件
            for call_args in mock_remove.call_args_list:
                removed_path = call_args[0][0]
                self.assertFalse(
                    removed_path.startswith(demo_dir),
                    f"不应删除 demo_documents 中的文件: {removed_path}"
                )

    # ─────────────────────────────────────────────────────────────
    # 10. update_document_category 更新分类
    # ─────────────────────────────────────────────────────────────
    def test_update_document_category(self):
        """update_document_category 能正确更新文档分类信息。"""
        self._insert_doc("cat_doc", "分类测试.pdf", status="completed")
        ok = self.sqlite_repo.update_document_category("cat_doc", "admission", "招生")
        self.assertTrue(ok)
        doc = self.sqlite_repo.get_document("cat_doc")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.get("category"), "admission")
        self.assertEqual(doc.get("category_name"), "招生")

    def test_delete_documents_batch_does_not_delete_demo_documents_files(self):
        """delete_documents_batch 批量删除时不应物理删除 demo_documents 目录中的原始文件。"""
        demo_dir = str(settings.BASE_DIR / "demo_documents")
        fake_demo_file = os.path.join(demo_dir, "fake_demo_batch.txt")
        
        # 插入一个指向 demo_documents 目录的正常文档记录
        self._insert_doc("demo_batch_ok", "fake_demo_batch.txt", status="completed",
                         file_path=fake_demo_file)
        
        # 执行批量删除（不应删除 demo_documents 中的文件）
        with patch("os.remove") as mock_remove:
            result = self.admin_service.delete_documents_batch(["demo_batch_ok"])
            self.assertEqual(result["deleted"], 1)
            # 确认 os.remove 没有被调用于 demo_dir 下的文件
            for call_args in mock_remove.call_args_list:
                removed_path = call_args[0][0]
                self.assertFalse(
                    removed_path.startswith(demo_dir),
                    f"批量删除不应删除 demo_documents 中的文件: {removed_path}"
                )


if __name__ == "__main__":
    unittest.main()
