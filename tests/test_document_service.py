import os
import unittest
from unittest.mock import MagicMock, patch
from services.document_service import DocumentService

class TestDocumentService(unittest.TestCase):
    def setUp(self):
        # 使用较小的切片大小，便于在测试中进行精确断言
        self.doc_service = DocumentService(chunk_size=100, chunk_overlap=20)
        self.temp_txt_path = "data/test_temp.txt"
        self.mock_pdf_path = "mock_file.pdf"
        self.mock_docx_path = "mock_file.docx"
        
        # 创建物理占位文件以通过 os.path.exists 校验
        with open(self.mock_pdf_path, 'w') as f:
            f.write("")
        with open(self.mock_docx_path, 'w') as f:
            f.write("")

    def tearDown(self):
        for path in [self.temp_txt_path, self.mock_pdf_path, self.mock_docx_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    def test_parse_txt(self):
        # 1. 写入一段测试文本（包含标点符号，字数超过100字以触发切分）
        # 复制文本以确保总长度显著大于 100 字符 (此处约为 200 字符)
        test_text = (
            "这是第一句，用于测试文本切分器的效果。接下来是第二句，我们将继续写入更多的中文字符以测试其切分逻辑。"
            "这是第三句，这里会有更多内容，目的是为了超过设定的100字长度限制。希望能正常切分为多个片段！"
            "这是第四句，额外添加用来把字符数堆叠到两百个字以上。现在的总长度绝对超过一百个字符了，应当被正常分割。"
        )
        os.makedirs(os.path.dirname(self.temp_txt_path), exist_ok=True)
        with open(self.temp_txt_path, 'w', encoding='utf-8') as f:
            f.write(test_text)

        # 2. 解析文档
        chunks = self.doc_service.parse_document(self.temp_txt_path, "txt")

        # 3. 断言校验
        self.assertGreater(len(chunks), 1)
        for i, chunk in enumerate(chunks):
            self.assertIsNone(chunk["page_number"])
            self.assertEqual(chunk["chunk_index"], i)
            self.assertTrue(len(chunk["text"]) > 0)

    @patch("pypdf.PdfReader")
    def test_parse_pdf_with_page_numbers(self, mock_pdf_reader):
        # 1. 模拟 PdfReader
        mock_reader_inst = MagicMock()
        mock_pdf_reader.return_value = mock_reader_inst

        # 模拟有 2 页
        mock_page_1 = MagicMock()
        mock_page_1.extract_text.return_value = "这是第一页的参考文本内容。用于测试PDF按页提取。"
        
        mock_page_2 = MagicMock()
        mock_page_2.extract_text.return_value = "这是第二页的参考文本内容。我们要确保第二页的页码正确关联。"

        mock_reader_inst.pages = [mock_page_1, mock_page_2]

        # 2. 调用解析
        chunks = self.doc_service.parse_document(self.mock_pdf_path, "pdf")

        # 3. 断言校验
        self.assertEqual(len(chunks), 2)
        
        self.assertEqual(chunks[0]["page_number"], 1)
        self.assertEqual(chunks[0]["chunk_index"], 0)
        self.assertIn("第一页", chunks[0]["text"])

        self.assertEqual(chunks[1]["page_number"], 2)
        self.assertEqual(chunks[1]["chunk_index"], 1)
        self.assertIn("第二页", chunks[1]["text"])

    @patch("docx.Document")
    def test_parse_docx(self, mock_docx_document):
        # 1. 模拟 Word 结构
        mock_doc_inst = MagicMock()
        mock_docx_document.return_value = mock_doc_inst

        # 模拟段落
        p1 = MagicMock()
        p1.text = "Word段落第一部分。"
        p2 = MagicMock()
        p2.text = "Word段落第二部分内容。"
        mock_doc_inst.paragraphs = [p1, p2]
        
        # 模拟空表格
        mock_doc_inst.tables = []

        # 2. 调用解析
        chunks = self.doc_service.parse_document(self.mock_docx_path, "docx")

        # 3. 断言校验
        self.assertTrue(len(chunks) >= 1)
        self.assertIsNone(chunks[0]["page_number"])
        self.assertEqual(chunks[0]["chunk_index"], 0)
        self.assertIn("Word", chunks[0]["text"])

if __name__ == '__main__':
    unittest.main()
