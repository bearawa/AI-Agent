# -*- coding: utf-8 -*-
"""
AIZS 知识库管理服务层
提供单文档级联删除、批量删除和失败记录一键清理功能。
"""
import os
from typing import Dict, Any, List
from repositories import sqlite_repository
from repositories.chroma_repository import ChromaRepository
from utils.logger import logger

class KnowledgeAdminService:
    def __init__(self):
        """
        初始化知识库管理服务。
        """
        self.chroma_repo = ChromaRepository()

    def delete_document(self, doc_id: str) -> bool:
        """
        级联且强一致性地删除一个文档：
        1. 读取 SQLite 中文档的信息，获得物理文件路径 file_path
        2. 清理向量数据库 (ChromaDB) 中的文档向量切片
        3. 清理关系数据库 (SQLite) 中的 message_sources 引用记录
        4. 清理关系数据库 (SQLite) 中的 documents 文档表记录
        5. 物理删除磁盘上的原始文件
        """
        logger.info(f"开始执行文档级联删除，文档 ID: {doc_id}")

        # 1. 查找文档以获取 file_path
        doc = None
        try:
            with sqlite_repository.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM documents WHERE doc_id = ?', (doc_id,))
                row = cursor.fetchone()
                if row:
                    doc = dict(row)
        except Exception as e:
            logger.error(f"级联删除前查询文档详情失败: {e}")
            return False

        if not doc:
            logger.warning(f"删除失败：未在数据库中找到 ID 为 {doc_id} 的文档")
            return False

        file_path = doc.get("file_path")
        file_name = doc.get("file_name")

        # 2. 清理 ChromaDB 中的切片向量
        chroma_success = self.chroma_repo.delete_by_doc_id(doc_id)
        if not chroma_success:
            logger.warning(f"级联删除警告：从向量库中删除文档 {doc_id} 向量失败，继续后续清理")

        # 3. 清理 SQLite 中的 message_sources 引用记录
        sources_success = sqlite_repository.delete_message_sources_by_doc_id(doc_id)
        if not sources_success:
            logger.warning(f"级联删除警告：清理 message_sources 引用关联失败，继续后续清理")

        # 4. 从 SQLite 的 documents 中删除记录
        db_success = sqlite_repository.delete_document_record(doc_id)
        if not db_success:
            logger.error(f"级联删除失败：从 documents 中删除记录失败 (Doc ID: {doc_id})")
            return False

        # 5. 删除物理文件（安全检查：不物理删除 demo_documents 目录下的原始演示文档）
        from config import settings
        demo_dir = str(settings.BASE_DIR / "demo_documents")

        if file_path and os.path.exists(file_path):
            if not os.path.abspath(file_path).startswith(os.path.abspath(demo_dir)):
                try:
                    os.remove(file_path)
                    logger.info(f"成功删除物理文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除物理文件 {file_path} 异常: {e}")
            else:
                logger.info(f"安全策略限制：文件位于演示文档目录，跳过物理文件删除: {file_path}")
        else:
            logger.warning(f"物理文件不存在，跳过文件删除: {file_path}")

        logger.info(f"文档 '{file_name}' (ID: {doc_id}) 级联删除成功完成")
        return True

    def delete_documents_batch(self, doc_ids: List[str]) -> Dict[str, Any]:
        """
        批量级联删除多个文档。内部逐个调用 delete_document，每个独立 try/except，互不影响。

        返回结构：
        {
            "total": int,
            "deleted": int,
            "failed": int,
            "items": [
                {"doc_id": str, "file_name": str, "status": "deleted"|"failed", "message": str}
            ]
        }
        """
        result = {"total": len(doc_ids), "deleted": 0, "failed": 0, "items": []}

        if not doc_ids:
            logger.warning("批量删除调用时传入空列表，直接返回")
            return result

        logger.info(f"开始批量删除文档，共 {len(doc_ids)} 个")

        # 批量获取文档信息，避免 N+1 查询问题
        docs = sqlite_repository.get_documents_by_ids(doc_ids)
        docs_map = {doc["doc_id"]: doc for doc in docs}

        for doc_id in doc_ids:
            file_name = doc_id  # 默认值
            try:
                doc = docs_map.get(doc_id)
                if not doc:
                    result["failed"] += 1
                    result["items"].append({
                        "doc_id": doc_id,
                        "file_name": file_name,
                        "status": "failed",
                        "message": "数据库中未找到该文档记录"
                    })
                    logger.warning(f"批量删除：文档 {doc_id} 不存在，跳过")
                    continue

                file_name = doc.get("file_name", doc_id)
                success = self.delete_document(doc_id)

                if success:
                    result["deleted"] += 1
                    result["items"].append({
                        "doc_id": doc_id,
                        "file_name": file_name,
                        "status": "deleted",
                        "message": "删除成功"
                    })
                    logger.info(f"批量删除：文档 '{file_name}' ({doc_id}) 删除成功")
                else:
                    result["failed"] += 1
                    result["items"].append({
                        "doc_id": doc_id,
                        "file_name": file_name,
                        "status": "failed",
                        "message": "级联删除执行失败，请查看系统日志"
                    })
                    logger.error(f"批量删除：文档 '{file_name}' ({doc_id}) 删除失败")

            except Exception as e:
                result["failed"] += 1
                result["items"].append({
                    "doc_id": doc_id,
                    "file_name": file_name,
                    "status": "failed",
                    "message": f"删除时发生异常: {str(e)}"
                })
                logger.error(f"批量删除：文档 {doc_id} 发生异常: {e}")

        logger.info(
            f"批量删除完成 - 总计: {result['total']}, "
            f"成功: {result['deleted']}, 失败: {result['failed']}"
        )
        return result

    def clear_failed_documents(self) -> Dict[str, Any]:
        """
        一键清理所有导入失败状态的文档记录及其残留资源。

        清理范围：
        1. documents 表中失败状态记录（failed/error/import_failed/processing_failed）
        2. ChromaDB 中可能残留的向量切片
        3. data/raw_documents 中可能残留的原始上传文件（不含 demo_documents 原始资料）
        4. message_sources 中引用该 doc_id 的脏引用

        绝对不清理：成功状态文档、demo_documents 原始演示资料、.env、数据库本身。

        返回结构：
        {
            "total": int,
            "cleared": int,
            "failed": int,
            "items": [
                {"doc_id": str, "file_name": str, "original_status": str, "result": "cleared"|"failed", "message": str}
            ]
        }
        """
        result = {"total": 0, "cleared": 0, "failed": 0, "items": []}

        failed_docs = sqlite_repository.list_failed_documents()
        if not failed_docs:
            logger.info("清理失败记录：当前没有失败状态文档，无需清理")
            return result

        result["total"] = len(failed_docs)
        logger.info(f"开始清理失败导入记录，共 {len(failed_docs)} 条")

        from config import settings
        demo_dir = str(settings.BASE_DIR / "demo_documents")

        for doc in failed_docs:
            doc_id = doc.get("doc_id", "")
            file_name = doc.get("file_name", "未知文件")
            original_status = doc.get("status", "failed")
            file_path = doc.get("file_path", "")

            try:
                # 1. 清理 ChromaDB 中可能残留的向量
                try:
                    self.chroma_repo.delete_by_doc_id(doc_id)
                    logger.info(f"清理失败记录：已清理 ChromaDB 中文档 {doc_id} 的残留向量")
                except Exception as chroma_err:
                    logger.warning(f"清理失败记录：ChromaDB 清理异常（非致命）: {chroma_err}")

                # 2. 清理 message_sources 脏引用
                sqlite_repository.delete_message_sources_by_doc_id(doc_id)

                # 3. 删除物理文件（安全检查：不删 demo_documents 原始资料）
                if file_path and os.path.exists(file_path):
                    if not file_path.startswith(demo_dir):
                        try:
                            os.remove(file_path)
                            logger.info(f"清理失败记录：已删除残留物理文件 {file_path}")
                        except Exception as file_err:
                            logger.warning(f"清理失败记录：删除残留文件失败（非致命）: {file_err}")
                    else:
                        logger.warning(f"清理失败记录：文件位于 demo_documents，跳过物理删除: {file_path}")

                # 4. 从 documents 表删除记录
                db_ok = sqlite_repository.delete_document_record(doc_id)
                if db_ok:
                    result["cleared"] += 1
                    result["items"].append({
                        "doc_id": doc_id,
                        "file_name": file_name,
                        "original_status": original_status,
                        "result": "cleared",
                        "message": "清理成功"
                    })
                    logger.info(f"清理失败记录：文档 '{file_name}' ({doc_id}) 清理完成")
                else:
                    result["failed"] += 1
                    result["items"].append({
                        "doc_id": doc_id,
                        "file_name": file_name,
                        "original_status": original_status,
                        "result": "failed",
                        "message": "SQLite 记录删除失败，请查看系统日志"
                    })

            except Exception as e:
                result["failed"] += 1
                result["items"].append({
                    "doc_id": doc_id,
                    "file_name": file_name,
                    "original_status": original_status,
                    "result": "failed",
                    "message": f"清理时发生异常: {str(e)}"
                })
                logger.error(f"清理失败记录：处理文档 {doc_id} 时异常: {e}")

        logger.info(
            f"失败记录清理完成 - 总计: {result['total']}, "
            f"已清理: {result['cleared']}, 失败: {result['failed']}"
        )
        return result
