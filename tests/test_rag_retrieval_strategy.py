import unittest
from unittest.mock import MagicMock, patch
from config import settings
from services.rag_service import RAGService
from services.tool_registry import search_campus_knowledge
from services.llm_service import LLMService

class TestRAGRetrievalStrategy(unittest.TestCase):
    def setUp(self):
        self.rag_service = RAGService()
        # 设定一个恒定的阈值进行测试
        settings.RAG_DISTANCE_THRESHOLD = 0.8

    @patch("services.rag_service.EmbeddingService.get_embedding")
    @patch("repositories.chroma_repository.ChromaRepository.query_similar_chunks")
    def test_intent_academic_but_logistics_more_relevant(self, mock_query_similar, mock_get_embedding):
        """
        测试：当提问意图为 academic (学务)，但 logistics (后勤) 分类中有更相关的内容时，
        最终应优先返回 logistics 中的高相似度内容（证明分类加权未压过真实相似度，且未被硬过滤阻断）。
        """
        mock_get_embedding.return_value = [0.1, 0.2]

        chunk_logistics = {
            "chunk_id": "chunk_logistics_1",
            "doc_id": "doc_logistics",
            "file_name": "图书馆指南.pdf",
            "page_number": 1,
            "chunk_index": 0,
            "source_text": "图书馆开放时间为早上8点到晚上10点",
            "similarity_distance": 0.3,
            "category": "logistics",
            "category_name": "后勤"
        }

        chunk_academic = {
            "chunk_id": "chunk_academic_1",
            "doc_id": "doc_academic",
            "file_name": "奖学金办法.pdf",
            "page_number": 2,
            "chunk_index": 1,
            "source_text": "国家奖学金申请要求成绩排名前10%",
            "similarity_distance": 0.6,
            "category": "academic",
            "category_name": "学务"
        }

        def mock_query(embedding, top_k=5, category=None):
            if category == "academic":
                return [chunk_academic]
            elif category == "logistics":
                return [chunk_logistics]
            elif category == "general":
                return []
            else:
                # 全库检索
                return [chunk_logistics, chunk_academic]

        mock_query_similar.side_effect = mock_query

        # 执行检索，主意图为 academic，置信度 0.9 (符合分类增强触发)
        results = self.rag_service.retrieve(
            query="图书馆几点关门？",
            intent="academic",
            intent_confidence=0.9,
            top_k=5
        )

        # 验证是否两个都召回了，且 logistics 排在第一位（0.3 优于 0.6 - 0.03 = 0.57）
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["chunk_id"], "chunk_logistics_1")
        self.assertEqual(results[1]["chunk_id"], "chunk_academic_1")

    @patch("services.rag_service.EmbeddingService.get_embedding")
    @patch("repositories.chroma_repository.ChromaRepository.query_similar_chunks")
    def test_fallback_to_global_when_category_empty(self, mock_query_similar, mock_get_embedding):
        """
        测试：当分类检索为空时，应自动退回到全库检索。
        """
        mock_get_embedding.return_value = [0.1, 0.2]

        chunk_global = {
            "chunk_id": "chunk_global_1",
            "doc_id": "doc_global",
            "file_name": "全局参考.pdf",
            "page_number": 1,
            "chunk_index": 5,
            "source_text": "这是一个全局性的参考资料",
            "similarity_distance": 0.4,
            "category": "other",
            "category_name": "其他"
        }

        def mock_query(embedding, top_k=5, category=None):
            if category == "academic":
                return []
            elif category == "general":
                return []
            else:
                return [chunk_global]

        mock_query_similar.side_effect = mock_query

        results = self.rag_service.retrieve(
            query="任何测试问题",
            intent="academic",
            intent_confidence=0.8,
            top_k=5
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "chunk_global_1")

    @patch("services.rag_service.EmbeddingService.get_embedding")
    @patch("repositories.chroma_repository.ChromaRepository.query_similar_chunks")
    def test_fallback_when_category_distance_large(self, mock_query_similar, mock_get_embedding):
        """
        测试：当分类检索结果距离过大（或只有过大结果被过滤）时，应从全库补充更好距离的结果。
        """
        mock_get_embedding.return_value = [0.1, 0.2]

        chunk_academic_far = {
            "chunk_id": "chunk_far",
            "doc_id": "doc_far",
            "file_name": "学务指南.pdf",
            "page_number": 1,
            "similarity_distance": 0.85,  # 超过 0.8 阈值
            "category": "academic",
            "category_name": "学务"
        }

        chunk_logistics_near = {
            "chunk_id": "chunk_near",
            "doc_id": "doc_near",
            "file_name": "后勤指南.pdf",
            "page_number": 2,
            "similarity_distance": 0.3,   # 很近
            "category": "logistics",
            "category_name": "后勤"
        }

        def mock_query(embedding, top_k=5, category=None):
            if category == "academic":
                return [chunk_academic_far]
            elif category == "general":
                return []
            else:
                return [chunk_academic_far, chunk_logistics_near]

        mock_query_similar.side_effect = mock_query

        results = self.rag_service.retrieve(
            query="测试问题",
            intent="academic",
            intent_confidence=0.85,
            top_k=5
        )

        # 默认阈值是 0.8，far 应该被过滤掉，只剩下 near (0.3)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "chunk_near")

    @patch("services.rag_service.EmbeddingService.get_embedding")
    @patch("repositories.chroma_repository.ChromaRepository.query_similar_chunks")
    def test_general_category_always_participates(self, mock_query_similar, mock_get_embedding):
        """
        测试：general 类文档应参与所有检索。
        """
        mock_get_embedding.return_value = [0.1, 0.2]

        chunk_general = {
            "chunk_id": "chunk_general_1",
            "doc_id": "doc_general",
            "file_name": "通用手册.pdf",
            "page_number": 1,
            "similarity_distance": 0.5,
            "category": "general",
            "category_name": "通用资料"
        }

        chunk_academic = {
            "chunk_id": "chunk_academic_1",
            "doc_id": "doc_academic",
            "file_name": "学务政策.pdf",
            "page_number": 2,
            "similarity_distance": 0.55,
            "category": "academic",
            "category_name": "学务"
        }

        def mock_query(embedding, top_k=5, category=None):
            if category == "academic":
                return [chunk_academic]
            elif category == "general":
                return [chunk_general]
            else:
                return [chunk_academic, chunk_general]

        mock_query_similar.side_effect = mock_query

        results = self.rag_service.retrieve(
            query="测试",
            intent="academic",
            intent_confidence=0.85,
            top_k=5
        )

        # 应当同时包含学术和通用资料
        ids = [r["chunk_id"] for r in results]
        self.assertIn("chunk_general_1", ids)
        self.assertIn("chunk_academic_1", ids)

    @patch("services.rag_service.EmbeddingService.get_embedding")
    @patch("repositories.chroma_repository.ChromaRepository.query_similar_chunks")
    def test_boost_not_overpowering_distance(self, mock_query_similar, mock_get_embedding):
        """
        测试：分类加权（如减去 0.03）不能压过明显更相关的全库结果。
        例如：academic 距离为 0.5，logistics 距离为 0.44，
        academic 虽然有 0.03 的加权（有效分数 0.47），但 logistics (有效分数 0.44) 仍应排在第一。
        """
        mock_get_embedding.return_value = [0.1, 0.2]

        chunk_academic = {
            "chunk_id": "chunk_acad",
            "similarity_distance": 0.5,
            "category": "academic",
            "category_name": "学务"
        }

        chunk_logistics = {
            "chunk_id": "chunk_logi",
            "similarity_distance": 0.44,
            "category": "logistics",
            "category_name": "后勤"
        }

        def mock_query(embedding, top_k=5, category=None):
            if category == "academic":
                return [chunk_academic]
            elif category == "general":
                return []
            else:
                return [chunk_academic, chunk_logistics]

        mock_query_similar.side_effect = mock_query

        results = self.rag_service.retrieve(
            query="测试问题",
            intent="academic",
            intent_confidence=0.85,
            top_k=5
        )

        # 虽然 academic 加权后 effective_score = 0.47，但 logistics (0.44) 更优，应该排在前面
        self.assertEqual(results[0]["chunk_id"], "chunk_logi")

    @patch("services.tool_registry._rag_service.retrieve")
    def test_search_campus_knowledge_tool_soft_filter(self, mock_retrieve):
        """
        测试：search_campus_knowledge 工具不应被 category 硬过滤。
        并且当没有结果时，应返回特定的中文提示。
        """
        # 1. 模拟 retrieve 返回结果
        mock_retrieve.return_value = [
            {
                "doc_id": "doc_1",
                "file_name": "图书馆指南.pdf",
                "category_name": "后勤",
                "page_number": 2,
                "chunk_index": 1,
                "similarity_distance": 0.4,
                "source_text": "图书馆几点关门"
            }
        ]

        # 调用工具，传 category='academic'，但由于是软检索，能返回 logistics 类别的内容
        res = search_campus_knowledge("图书馆", category="academic")
        self.assertEqual(res["chunks_count"], 1)
        self.assertEqual(res["results"][0]["file_name"], "图书馆指南.pdf")
        self.assertEqual(res["results"][0]["category_name"], "后勤")

        # 2. 模拟 retrieve 返回空，测试明确的中文返回
        mock_retrieve.return_value = []
        res_empty = search_campus_knowledge("不存在的内容")
        self.assertEqual(res_empty["results"], [])
        self.assertIn("当前知识库未检索到足够相关资料", res_empty["message"])

    def test_llm_prompt_boundaries_instruction(self):
        """
        测试：Prompt 中应明确说明分类不是检索边界。
        """
        llm_service = LLMService()
        mock_client = MagicMock()
        llm_service._client = mock_client
        llm_service.api_key = "fake_api_key"
        
        try:
            list(llm_service.chat_stream([], [{"file_name": "a.txt", "page_number": 1, "chunk_index": 0, "source_text": "text"}], "query", "academic", 0.9))
        except Exception:
            pass
            
        mock_client.chat.completions.create.assert_called()
        call_args = mock_client.chat.completions.create.call_args[1]
        messages = call_args["messages"]
        
        system_msg = next(m for m in messages if m["role"] == "system")
        user_msg = next(m for m in messages if m["role"] == "user")
        
        self.assertIn("分类只表示资料管理标签，不代表答案边界", system_msg["content"])
        self.assertIn("说明：该结果仅用于辅助理解问题，不作为限制检索范围的依据", user_msg["content"])

if __name__ == "__main__":
    unittest.main()
