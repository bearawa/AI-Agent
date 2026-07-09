import chromadb
from typing import List, Dict, Any, Optional
from config import settings
from utils.logger import logger

class ChromaRepository:
    def __init__(self):
        """
        初始化 ChromaDB 仓库，使用本地持久化模式。
        """
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        self.collection_name = "campus_knowledge"
        # 延迟初始化 collection，确保安全
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            # 创建或获取集合
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"} # 使用余弦距离进行度量
            )
        return self._collection

    def add_chunks(
        self,
        doc_id: str,
        file_name: str,
        file_type: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        category: str = "other",
        category_name: str = "其他"
    ) -> bool:
        """
        向向量库添加文档切片和其对应的 Embedding 向量。
        :param doc_id: 文档 ID
        :param file_name: 文件名
        :param file_type: 文件类型 (pdf, docx, txt)
        :param chunks: 切片文本列表
        :param embeddings: 由 embedding_service 生成的向量列表
        :param metadatas: 对应的元数据列表，其中必须包含 page_number (对 PDF) 或 chunk_index
        :param category: 文档分类
        :param category_name: 文档中文分类名
        """
        if not chunks:
            logger.warning(f"文件 {file_name} 的切片列表为空，跳过向量库导入")
            return False

        try:
            ids = [f"doc_{doc_id}_chunk_{i}" for i in range(len(chunks))]
            
            # 补齐元数据
            for i, meta in enumerate(metadatas):
                meta["doc_id"] = doc_id
                meta["file_name"] = file_name
                meta["file_type"] = file_type
                meta["category"] = category
                meta["category_name"] = category_name
                # 显式确保 page_number 存在，若是 None 也不要漏掉
                if "page_number" not in meta:
                    meta["page_number"] = -1  # 用 -1 代表无页码

            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=chunks
            )
            logger.info(f"成功将文档 {file_name} (ID: {doc_id}) 的 {len(chunks)} 个切片添加到向量库")
            return True
        except Exception as e:
            logger.error(f"向向量库添加数据时发生异常: {e}")
            # 异常时进行事务性回滚：删除刚才可能部分导入的 doc_id
            self.delete_by_doc_id(doc_id)
            raise e

    def query_similar_chunks(self, query_embedding: List[float], top_k: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        根据查询向量检索最相似的切片。
        返回标准化后的结构体列表：
        [
          {
            "chunk_id": str,
            "doc_id": str,
            "file_name": str,
            "page_number": int,
            "chunk_index": int,
            "source_text": str,
            "similarity_distance": float
          }
        ]
        """
        try:
            # 如果指定了 category 过滤条件，则加入 where 条件
            where_filter = None
            if category:
                where_filter = {"category": category}

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter
            )

            # 解析 Chroma 返回结果
            # Chroma 返回格式：{"ids": [[id1, id2...]], "distances": [[d1, d2...]], "metadatas": [[m1, m2...]], "documents": [[doc1, doc2...]]}
            formatted_results = []
            
            # 若结果为空
            if not results or not results.get("ids") or len(results["ids"][0]) == 0:
                return []

            ids = results["ids"][0]
            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            documents = results.get("documents", [[]])[0]

            for i in range(len(ids)):
                meta = metadatas[i] if i < len(metadatas) else {}
                # 转换元数据中的 page_number (-1 转为 None)
                page_number = meta.get("page_number")
                if page_number == -1:
                    page_number = None

                formatted_results.append({
                    "chunk_id": ids[i],
                    "doc_id": meta.get("doc_id", ""),
                    "file_name": meta.get("file_name", ""),
                    "page_number": page_number,
                    "chunk_index": int(meta.get("chunk_index", 0)),
                    "source_text": documents[i] if i < len(documents) else "",
                    "similarity_distance": float(distances[i]) if i < len(distances) else 1.0,
                    "category": meta.get("category", "other"),
                    "category_name": meta.get("category_name", "未分类")
                })

            return formatted_results
        except Exception as e:
            logger.error(f"在向量库中查询相似切片发生异常: {e}")
            return []

    def delete_by_doc_id(self, doc_id: str) -> bool:
        """
        根据 doc_id 删除该文件对应的所有向量切片。
        """
        try:
            self.collection.delete(where={"doc_id": doc_id})
            logger.info(f"成功从向量库中删除文档 {doc_id} 的所有切片")
            return True
        except Exception as e:
            logger.error(f"从向量库中删除文档 {doc_id} 的切片失败: {e}")
            return False
