# -*- coding: utf-8 -*-
"""
批量导入服务单元测试
"""
import unittest
from unittest.mock import MagicMock, patch
import io
import zipfile
import os
from pathlib import Path
from services.batch_import_service import BatchImportService

class TestBatchImportService(unittest.TestCase):

    @patch('services.batch_import_service.RAGService')
    @patch('services.batch_import_service.sqlite_repository')
    def test_multi_file_import_error_isolation(self, mock_sqlite, mock_rag_class):
        """
        测试多文件导入的隔离性：一个文件处理失败，不影响其他文件入库。
        """
        mock_rag = mock_rag_class.return_value
        
        # 模拟 import_document，第一个成功，第二个抛出系统异常，第三个成功
        mock_rag.import_document.side_effect = ["id-1", RuntimeError("解析出错"), "id-3"]
        
        # 使用更健全的条件返回值来处理 get_document，避免执行顺序错乱带来的影响
        def mock_get_doc(doc_id):
            if doc_id == "id-1":
                return {"chunk_count": 5}
            elif doc_id == "id-3":
                return {"chunk_count": 8}
            return None
            
        mock_sqlite.get_document.side_effect = mock_get_doc
        
        mock_files = [
            MagicMock(name="file1.pdf", spec=["name", "read"]),
            MagicMock(name="file2.docx", spec=["name", "read"]),
            MagicMock(name="file3.txt", spec=["name", "read"])
        ]
        mock_files[0].name = "file1.pdf"
        mock_files[0].read.return_value = b"file1 content"
        mock_files[1].name = "file2.docx"
        mock_files[1].read.return_value = b"file2 content"
        mock_files[2].name = "file3.txt"
        mock_files[2].read.return_value = b"file3 content"
        
        import_service = BatchImportService()
        results = import_service.import_uploaded_files(mock_files, "admission")
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["chunk_count"], 5)
        
        self.assertEqual(results[1]["status"], "failed")
        self.assertIn("系统错误: 解析出错", results[1]["error_message"])
        
        self.assertEqual(results[2]["status"], "success")
        self.assertEqual(results[2]["chunk_count"], 8)

    @patch('services.batch_import_service.RAGService')
    def test_skipped_duplicate_file(self, mock_rag_class):
        """
        测试重复文件跳过，返回 skipped 状态而不判定为 failed。
        """
        mock_rag = mock_rag_class.return_value
        # 模拟抛出 ValueError 表示文件已在知识库中导入
        mock_rag.import_document.side_effect = ValueError("该文件已在知识库中导入（文件名：test.pdf），请勿重复上传。")
        
        import_service = BatchImportService()
        res = import_service.import_single_file(b"content", "test.pdf", "academic")
        
        self.assertEqual(res["status"], "skipped")
        self.assertEqual(res["error_message"], "重复文件已被跳过")

    @patch('services.batch_import_service.RAGService')
    @patch('services.batch_import_service.sqlite_repository')
    def test_zip_import_supported_only(self, mock_sqlite, mock_rag_class):
        """
        测试 ZIP 压缩包导入时：只处理 PDF, DOCX, TXT，其余文件（如 PNG）被跳过。
        """
        mock_rag = mock_rag_class.return_value
        mock_rag.import_document.return_value = "doc-id"
        mock_sqlite.get_document.return_value = {"chunk_count": 3}
        
        # 内存中构建 ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("docs/doc1.pdf", b"pdf data")
            zf.writestr("docs/image1.png", b"image data") # 不支持，应跳过
            zf.writestr("doc2.txt", b"txt data")
            
        zip_bytes = zip_buffer.getvalue()
        
        import_service = BatchImportService()
        results = import_service.import_zip_file(zip_bytes, "logistics")
        
        # 结果列表中应该包含 3 项，其中图片为 skipped
        self.assertEqual(len(results), 3)
        filenames = [res["file_name"] for res in results]
        self.assertIn("doc1.pdf", filenames)
        self.assertIn("doc2.txt", filenames)
        self.assertIn("docs/image1.png", filenames)
        
        # 验证各项状态
        doc1_res = next(r for r in results if r["file_name"] == "doc1.pdf")
        doc2_res = next(r for r in results if r["file_name"] == "doc2.txt")
        img_res = next(r for r in results if r["file_name"] == "docs/image1.png")
        
        self.assertEqual(doc1_res["status"], "success")
        self.assertEqual(doc2_res["status"], "success")
        self.assertEqual(img_res["status"], "skipped")
        self.assertEqual(img_res["error_message"], "不支持的文件类型，已跳过")

    @patch('services.batch_import_service.RAGService')
    def test_zip_slip_protection(self, mock_rag_class):
        """
        测试 Zip Slip 路径穿越防御：拒绝解压到目标目录外的文件，并返回 failed 状态及中文安全错误。
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            # 路径穿越文件名
            zf.writestr("../../etc/passwd.txt", b"malicious content")
            
        zip_bytes = zip_buffer.getvalue()
        
        import_service = BatchImportService()
        results = import_service.import_zip_file(zip_bytes, "other")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "failed")
        self.assertIn("安全验证失败", results[0]["error_message"])

    def test_build_import_report(self):
        """
        测试批量导入报告汇总数据计算准确性。
        """
        mock_results = [
            {"status": "success", "chunk_count": 10},
            {"status": "success", "chunk_count": 5},
            {"status": "skipped", "chunk_count": 0},
            {"status": "failed", "chunk_count": 0}
        ]
        
        import_service = BatchImportService()
        report = import_service.build_import_report(mock_results)
        
        self.assertEqual(report["total_files"], 4)
        self.assertEqual(report["success_count"], 2)
        self.assertEqual(report["skipped_count"], 1)
        self.assertEqual(report["failed_count"], 1)
        self.assertEqual(report["total_chunks"], 15)

    @patch('services.batch_import_service.Path.exists')
    def test_demo_documents_dir_missing(self, mock_exists):
        """
        测试当演示文档目录不存在时，返回特定的中文错误提示。
        """
        mock_exists.return_value = False
        
        import_service = BatchImportService()
        results = import_service.import_demo_documents()
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "failed")
        self.assertIn("demo_documents 不存在", results[0]["error_message"])
