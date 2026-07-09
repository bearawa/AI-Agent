import os
import uuid
from typing import List, Dict, Any, Optional
from config import settings
from utils.logger import logger
from utils.file_utils import calculate_file_hash, save_uploaded_file
from repositories import sqlite_repository
from repositories.chroma_repository import ChromaRepository
from services.embedding_service import EmbeddingService
from services.document_service import DocumentService

class RAGService:
    def __init__(self):
        """
        初始化 RAG 服务，协调文档解析、Embedding、向量数据库和关系数据库。
        """
        self.chroma_repo = ChromaRepository()
        self.embedding_service = EmbeddingService()
        self.doc_service = DocumentService(
            chunk_size=500,  # 约 400~600 字符
            chunk_overlap=100  # 重叠约 80~120 字符
        )

    def import_document(self, file_name: str, file_bytes: bytes, category: str = "other", category_name: str = "其他") -> str:
        """
        导入上传的文件到 RAG 系统中（解析 -> 向量化 -> 入向量库 -> 入关系库）。
        :param file_name: 原始文件名
        :param file_bytes: 文件二进制内容
        :param category: 文档分类
        :param category_name: 中文分类名
        :return: 返回生成的 doc_id
        """
        # 1. 计算文件哈希值并去重校验
        file_hash = calculate_file_hash(file_bytes)
        existing_doc = sqlite_repository.get_document_by_hash(file_hash)
        if existing_doc:
            logger.warning(f"检测到重复文件内容上传，文件名: {file_name}, 已存在 ID: {existing_doc['doc_id']}")
            raise ValueError(f"该文件已在知识库中导入（文件名：{existing_doc['file_name']}），请勿重复上传。")

        # 2. 检查是否有未删除的同名文档
        existing_name_doc = sqlite_repository.get_document_by_name(file_name)
        if existing_name_doc:
            logger.warning(f"检测到同名文件上传，文件名: {file_name}")
            raise ValueError(f"知识库中已存在同名文档（{file_name}），请修改文件名或在管理后台删除已有文档后再试。")

        # 3. 生成文档 ID 并保存到本地
        doc_id = str(uuid.uuid4())
        _, ext = os.path.splitext(file_name)
        file_type = ext.lower().lstrip('.')
        
        # 存到 raw_documents
        local_path = save_uploaded_file(file_name, file_bytes)

        # 4. 在 SQLite 中记录初始状态 (processing)
        success = sqlite_repository.save_document(
            doc_id=doc_id,
            file_name=file_name,
            file_path=local_path,
            file_type=file_type,
            file_hash=file_hash,
            status="processing",
            category=category,
            category_name=category_name
        )
        if not success:
            # 若记录 SQLite 失败，清理已保存的文件，并抛错
            if os.path.exists(local_path):
                os.remove(local_path)
            raise RuntimeError("在 SQLite 中记录文档信息失败")

        # 5. 解析、切片并向量化导入
        try:
            # 解析文档
            parsed_chunks = self.doc_service.parse_document(local_path, file_type)
            if not parsed_chunks:
                raise ValueError("该文档解析出的文本切片数量为 0")

            # 提取切片原文及组装元数据
            chunk_texts = [item["text"] for item in parsed_chunks]
            metadatas = [
                {
                    "page_number": item["page_number"] if item["page_number"] is not None else -1,
                    "chunk_index": item["chunk_index"]
                }
                for item in parsed_chunks
            ]

            # 批量获取 Embeddings 向量
            embeddings = self.embedding_service.get_embeddings_batch(chunk_texts)

            # 写入本地向量库
            self.chroma_repo.add_chunks(
                doc_id=doc_id,
                file_name=file_name,
                file_type=file_type,
                chunks=chunk_texts,
                embeddings=embeddings,
                metadatas=metadatas,
                category=category,
                category_name=category_name
            )

            # 更新 SQLite 记录为 completed 状态
            sqlite_repository.update_document_status(
                doc_id=doc_id,
                status="completed",
                chunk_count=len(parsed_chunks)
            )
            logger.info(f"文档 {file_name} 导入并向量化成功！")
            return doc_id

        except Exception as e:
            # 捕获异常后触发清理机制
            logger.error(f"导入文档 {file_name} 失败，开始清理残留数据: {e}")
            
            # 清理 Chroma 向量库
            self.chroma_repo.delete_by_doc_id(doc_id)
            
            # 更新 SQLite 记录为 failed 状态
            error_msg = str(e)
            sqlite_repository.update_document_status(
                doc_id=doc_id,
                status="failed",
                chunk_count=0,
                error_message=error_msg
            )
            raise RuntimeError(f"文档导入失败: {error_msg}")

    def retrieve(
        self,
        query: str,
        intent: Optional[str] = None,
        intent_confidence: Optional[float] = None,
        top_k: int = 5,
        use_category_boost: bool = True
    ) -> List[Dict[str, Any]]:
        """
        全库优先 + 分类增强 + 通用资料补充 + 自动回退 的 RAG 检索策略
        """
        logger.info(f"开始执行 RAG.retrieve，检索词: '{query}'，意图分类: '{intent}'，置信度: {intent_confidence}，Top K: {top_k}")
        
        try:
            # 1. 向量化检索词
            query_embedding = self.embedding_service.get_embedding(query)
            
            # 第一步：全库检索
            global_top_k = max(10, top_k * 2) # 全库检索 top_k 建议 8 或 10
            global_results = self.chroma_repo.query_similar_chunks(query_embedding, top_k=global_top_k)
            logger.info(f"第一步全库检索完成，召回 {len(global_results)} 个切片")
            
            # 第二步：分类增强检索（可选）
            category_results = []
            if use_category_boost and intent and intent not in ["other", "general"] and intent_confidence is not None and intent_confidence >= 0.75:
                category_results = self.chroma_repo.query_similar_chunks(query_embedding, top_k=5, category=intent)
                logger.info(f"第二步分类增强检索完成 (分类: '{intent}')，召回 {len(category_results)} 个切片")
            
            # 第三步：通用资料检索（可选）
            general_results = []
            general_results = self.chroma_repo.query_similar_chunks(query_embedding, top_k=5, category="general")
            if general_results:
                logger.info(f"第三步通用资料检索完成，召回 {len(general_results)} 个切片")
            
            # 第四步：合并去重
            seen_chunk_ids = set()
            merged_results = []
            
            for r in global_results + category_results + general_results:
                if r["chunk_id"] not in seen_chunk_ids:
                    seen_chunk_ids.add(r["chunk_id"])
                    merged_results.append(r)
                    
            logger.info(f"合并去重完成，共 {len(merged_results)} 个候选切片")
            
            # 第五步：重排序
            # 加权公式：
            # effective_score = similarity_distance
            # 如果 chunk.category == intent: effective_score = similarity_distance - 0.03
            # 如果 chunk.category == "general": effective_score = similarity_distance - 0.01
            for r in merged_results:
                dist = r["similarity_distance"]
                chunk_cat = r.get("category", "other")
                
                effective_score = dist
                if intent is not None and chunk_cat == intent:
                    effective_score = dist - 0.03
                elif chunk_cat == "general":
                    effective_score = dist - 0.01
                
                r["effective_score"] = effective_score
            
            # 按 effective_score 从小到大排序
            merged_results.sort(key=lambda x: x["effective_score"])
            
            # 第六步：阈值过滤
            threshold = settings.RAG_DISTANCE_THRESHOLD
            filtered_results = [r for r in merged_results if r["similarity_distance"] <= threshold]
            
            # 自动兜底阈值
            if not filtered_results and merged_results:
                fallback_threshold = threshold + 0.1
                filtered_results = [r for r in merged_results if r["similarity_distance"] <= fallback_threshold]
                logger.info(f"RAG 检索在原始阈值 {threshold} 下无结果，触发宽松兜底阈值 {fallback_threshold:.2f}，过滤召回 {len(filtered_results)} 个切片")
            else:
                logger.info(f"RAG 检索在原始阈值 {threshold} 下成功过滤召回 {len(filtered_results)} 个切片")
            
            # 取 top_k 个结果
            final_results = filtered_results[:top_k]
            return final_results
            
        except Exception as e:
            logger.error(f"执行 RAG 检索策略 retrieve 异常: {e}")
            raise e

    def search_relevant_chunks(self, query_text: str, top_k: Optional[int] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        根据用户问题（改写后的检索问题）在向量数据库中检索最相似的切片。
        保持接口向后兼容，调用全新的 retrieve 检索机制。
        """
        if not top_k:
            top_k = settings.RAG_TOP_K
        
        # 将传入的 category 作为 intent，置信度设为 1.0 以确保如果传入了非 other 分类，它能参与增强检索与加权
        intent_conf = 1.0 if category and category != "other" else None
        return self.retrieve(
            query=query_text,
            intent=category,
            intent_confidence=intent_conf,
            top_k=top_k,
            use_category_boost=True
        )
