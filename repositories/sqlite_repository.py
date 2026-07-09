import sqlite3
import datetime
import uuid
from typing import List, Dict, Any, Optional
from config import settings
from utils.logger import logger

def get_connection():
    """
    获取 SQLite 连接。
    """
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.row_factory = sqlite3.Row  # 返回字典格式的数据
    return conn

def get_table_columns(conn, table_name):
    """
    获取表的列名列表。
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def init_db():
    """
    初始化 SQLite 数据库及建表。
    支持在不破坏已有数据的前提下进行增量迁移。
    """
    logger.info("正在初始化 SQLite 数据库...")
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. documents 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                uploaded_at TEXT NOT NULL,
                status TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                error_message TEXT
            )
        ''')

        # 2. chat_sessions 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # 3. messages 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
            )
        ''')

        # 4. message_sources 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_sources (
                source_id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                chunk_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                page_number INTEGER,
                chunk_index INTEGER NOT NULL,
                source_text TEXT NOT NULL,
                similarity_distance REAL NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE
            )
        ''')
        
        # 5. feedback 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id TEXT PRIMARY KEY,
                message_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                rating TEXT NOT NULL,
                comment TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE
            )
        ''')
        
        # --- 增量迁移检查与升级 ---
        
        # documents 表的字段增量检查
        doc_cols = get_table_columns(conn, "documents")
        if "category" not in doc_cols:
            logger.info("增量迁移：向 documents 表添加 category 字段")
            cursor.execute("ALTER TABLE documents ADD COLUMN category TEXT DEFAULT 'other'")
        if "category_name" not in doc_cols:
            logger.info("增量迁移：向 documents 表添加 category_name 字段")
            cursor.execute("ALTER TABLE documents ADD COLUMN category_name TEXT DEFAULT '其他'")
        if "deleted_at" not in doc_cols:
            logger.info("增量迁移：向 documents 表添加 deleted_at 字段")
            cursor.execute("ALTER TABLE documents ADD COLUMN deleted_at TEXT")

        # messages 表的字段增量检查
        msg_cols = get_table_columns(conn, "messages")
        if "intent" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 intent 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN intent TEXT")
        if "intent_name" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 intent_name 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN intent_name TEXT")
        if "intent_confidence" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 intent_confidence 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN intent_confidence REAL")
        if "intent_reason" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 intent_reason 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN intent_reason TEXT")
        if "rewritten_query" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 rewritten_query 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN rewritten_query TEXT")
        if "has_source" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 has_source 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN has_source INTEGER DEFAULT 0")
        if "response_time_ms" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 response_time_ms 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN response_time_ms INTEGER")
        if "agent_mode" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 agent_mode 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN agent_mode INTEGER DEFAULT 0")
        if "tool_used" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 tool_used 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN tool_used INTEGER DEFAULT 0")
        if "quality_score" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 quality_score 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN quality_score INTEGER")
        if "is_low_quality" not in msg_cols:
            logger.info("增量迁移：向 messages 表添加 is_low_quality 字段")
            cursor.execute("ALTER TABLE messages ADD COLUMN is_low_quality INTEGER DEFAULT 0")

        # 6. tool_logs 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_logs (
                tool_log_id TEXT PRIMARY KEY,
                session_id TEXT,
                message_id TEXT,
                tool_name TEXT NOT NULL,
                tool_display_name TEXT,
                tool_args TEXT,
                tool_result TEXT,
                success INTEGER,
                error_message TEXT,
                elapsed_ms INTEGER,
                created_at TEXT NOT NULL
            )
        ''')

        # 7. agent_traces 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_traces (
                trace_id TEXT PRIMARY KEY,
                session_id TEXT,
                message_id TEXT,
                step_index INTEGER,
                step_type TEXT,
                step_title TEXT,
                step_detail TEXT,
                created_at TEXT NOT NULL
            )
        ''')

        # 8. quality_evaluations 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_evaluations (
                evaluation_id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                score INTEGER,
                is_low_quality INTEGER,
                issues TEXT,
                suggestion TEXT,
                evaluator TEXT,
                created_at TEXT NOT NULL
            )
        ''')

        conn.commit()
    logger.info("SQLite 数据库初始化与增量迁移完成")

# --- Documents 相关操作 ---

def save_document(doc_id: str, file_name: str, file_path: str, file_type: str, file_hash: str, status: str = "processing", category: str = "other", category_name: str = "其他") -> bool:
    """
    保存或初始化一个文档记录。
    """
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO documents (doc_id, file_name, file_path, file_type, file_hash, uploaded_at, status, category, category_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (doc_id, file_name, file_path, file_type, file_hash, now, status, category, category_name))
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"保存文档记录到数据库失败: {e}")
        return False

def get_document_by_name(file_name: str) -> Optional[Dict[str, Any]]:
    """
    根据文件名查找未删除的文档。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM documents WHERE file_name = ? AND (deleted_at IS NULL OR deleted_at = "")', (file_name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"通过文件名查询文档失败: {e}")
        return None

def update_document_status(doc_id: str, status: str, chunk_count: int = 0, error_message: str = None) -> bool:
    """
    更新文档状态和切片数量。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE documents
                SET status = ?, chunk_count = ?, error_message = ?
                WHERE doc_id = ?
            ''', (status, chunk_count, error_message, doc_id))
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"更新文档状态失败: {e}")
        return False

def get_document_by_hash(file_hash: str) -> Optional[Dict[str, Any]]:
    """
    根据文件内容哈希查找文档。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM documents WHERE file_hash = ?', (file_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"通过哈希查询文档失败: {e}")
        return None

def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
    """
    根据 doc_id 查询单个文档记录。
    兼容批量导入、ZIP 导入和知识库管理模块。
    """
    if not doc_id:
        return None
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT *
                FROM documents
                WHERE doc_id = ?
                  AND (deleted_at IS NULL OR deleted_at = '')
                  AND status != 'deleted'
            ''', (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"通过 doc_id 查询文档失败: {e}")
        return None

def list_documents() -> List[Dict[str, Any]]:
    """
    列出所有文档。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM documents ORDER BY uploaded_at DESC')
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error(f"查询文档列表失败: {e}")
        return []

def delete_document_record(doc_id: str) -> bool:
    """
    删除文档记录。用于导入失败时清理数据。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM documents WHERE doc_id = ?', (doc_id,))
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"删除文档记录失败: {e}")
        return False


def list_failed_documents() -> List[Dict[str, Any]]:
    """
    查询所有导入失败状态的文档记录。
    兼容以下失败状态：failed, error, import_failed, processing_failed。
    """
    failed_statuses = ('failed', 'error', 'import_failed', 'processing_failed')
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' for _ in failed_statuses)
            cursor.execute(
                f'SELECT * FROM documents WHERE status IN ({placeholders}) ORDER BY uploaded_at DESC',
                failed_statuses
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error(f"查询失败文档列表失败: {e}")
        return []


def delete_message_sources_by_doc_id(doc_id: str) -> bool:
    """
    删除 message_sources 表中引用指定 doc_id 文档的所有脏引用记录。
    在文档被物理删除前调用，清理关联的溯源引用。
    """
    if not doc_id:
        return False
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM message_sources WHERE doc_id = ?', (doc_id,))
            conn.commit()
        logger.info(f"已清理文档 {doc_id} 的 message_sources 引用记录")
        return True
    except sqlite3.Error as e:
        logger.error(f"清理 message_sources 引用失败 (doc_id={doc_id}): {e}")
        return False


def update_document_category(doc_id: str, category: str, category_name: str) -> bool:
    """
    更新文档的分类信息。支持批量修改分类场景。
    """
    if not doc_id:
        return False
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE documents SET category = ?, category_name = ? WHERE doc_id = ?',
                (category, category_name, doc_id)
            )
            conn.commit()
        logger.info(f"已更新文档 {doc_id} 分类为: {category_name}({category})")
        return True
    except sqlite3.Error as e:
        logger.error(f"更新文档分类失败 (doc_id={doc_id}): {e}")
        return False


# --- Chat Sessions 相关操作 ---

def create_chat_session(title: str, session_id: str = None) -> str:
    """
    创建一个新的会话。若未提供 session_id，则自动生成 UUID。
    返回 session_id。
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_sessions (session_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (session_id, title, now, now))
            conn.commit()
        logger.info(f"成功创建会话: {session_id}, 标题: {title}")
        return session_id
    except sqlite3.Error as e:
        logger.error(f"创建会话失败: {e}")
        raise e

def update_session_title(session_id: str, title: str) -> bool:
    """
    更新会话标题。
    """
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE chat_sessions
                SET title = ?, updated_at = ?
                WHERE session_id = ?
            ''', (title, now, session_id))
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"更新会话标题失败: {e}")
        return False

def list_chat_sessions() -> List[Dict[str, Any]]:
    """
    列出所有会话，按最后更新时间倒序。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # 顺便统计每个会话的消息数量
            cursor.execute('''
                SELECT s.session_id, s.title, s.created_at, s.updated_at, COUNT(m.message_id) as message_count
                FROM chat_sessions s
                LEFT JOIN messages m ON s.session_id = m.session_id
                GROUP BY s.session_id
                ORDER BY s.updated_at DESC
            ''')
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error(f"查询会话列表失败: {e}")
        return []

def delete_chat_session(session_id: str) -> bool:
    """
    级联删除会话及其对应的消息和引用来源。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # 开启外键约束支持以实现级联删除
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute('DELETE FROM chat_sessions WHERE session_id = ?', (session_id,))
            conn.commit()
        logger.info(f"成功级联删除会话: {session_id}")
        return True
    except sqlite3.Error as e:
        logger.error(f"级联删除会话失败: {e}")
        return False


# --- Messages 相关操作 ---

def save_message(
    session_id: str,
    role: str,
    content: str,
    message_id: str = None,
    intent: str = None,
    intent_name: str = None,
    intent_confidence: float = None,
    intent_reason: str = None,
    rewritten_query: str = None,
    has_source: int = 0,
    response_time_ms: int = None,
    agent_mode: int = 0,
    tool_used: int = 0,
    quality_score: int = None,
    is_low_quality: int = 0
) -> str:
    """
    保存一条对话消息。返回 message_id。
    并在写入消息后，自动更新会话的 updated_at。
    """
    if not message_id:
        message_id = str(uuid.uuid4())
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # 保存消息
            cursor.execute('''
                INSERT INTO messages (
                    message_id, session_id, role, content, created_at,
                    intent, intent_name, intent_confidence, intent_reason, rewritten_query, has_source, response_time_ms,
                    agent_mode, tool_used, quality_score, is_low_quality
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id, session_id, role, content, now,
                intent, intent_name, intent_confidence, intent_reason, rewritten_query, has_source, response_time_ms,
                agent_mode, tool_used, quality_score, is_low_quality
            ))
            
            # 更新会话的最后更新时间
            cursor.execute('''
                UPDATE chat_sessions
                SET updated_at = ?
                WHERE session_id = ?
            ''', (now, session_id))
            
            conn.commit()
        return message_id
    except sqlite3.Error as e:
        logger.error(f"保存消息失败: {e}")
        raise e

def get_chat_messages(session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    获取某会话的历史消息。
    :param limit: 限制获取消息的数量。如果设置，会获取最新 limit 条（但需要按时间正序排列返回）。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if limit:
                # 获取最新的 limit 条消息（排在后面的物理写入顺序最新的消息）
                cursor.execute('''
                    SELECT * FROM (
                        SELECT *, rowid FROM messages 
                        WHERE session_id = ? 
                        ORDER BY rowid DESC 
                        LIMIT ?
                    ) ORDER BY rowid ASC
                ''', (session_id, limit))
            else:
                cursor.execute('''
                    SELECT *, rowid FROM messages 
                    WHERE session_id = ? 
                    ORDER BY rowid ASC
                ''', (session_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error(f"查询历史消息失败: {e}")
        return []


# --- Message Sources 相关操作 ---

def save_message_sources(message_id: str, sources: List[Dict[str, Any]]) -> bool:
    """
    保存助手回答的原文来源列表。
    sources 列表项应包含: doc_id, chunk_id, file_name, page_number, chunk_index, source_text, similarity_distance
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            for src in sources:
                source_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO message_sources (
                        source_id, message_id, doc_id, chunk_id, file_name, page_number, chunk_index, source_text, similarity_distance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    source_id,
                    message_id,
                    src['doc_id'],
                    src['chunk_id'],
                    src['file_name'],
                    src.get('page_number'),
                    src['chunk_index'],
                    src['source_text'],
                    src['similarity_distance']
                ))
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"保存消息来源失败: {e}")
        return False

def get_message_sources(message_id: str) -> List[Dict[str, Any]]:
    """
    获取某条消息的所有原文引用来源。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM message_sources 
                WHERE message_id = ?
                ORDER BY similarity_distance ASC
            ''', (message_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error(f"查询消息来源失败: {e}")
        return []


# --- Feedback 相关操作 ---

def save_or_update_feedback(message_id: str, session_id: str, rating: str, comment: str = "") -> bool:
    """
    保存或更新一条消息的反馈。如果已存在则更新。
    并在更新反馈后，触发问答质量的重新评估。
    """
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    feedback_id = str(uuid.uuid4())
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT feedback_id FROM feedback WHERE message_id = ?', (message_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute('''
                    UPDATE feedback
                    SET rating = ?, comment = ?, created_at = ?
                    WHERE message_id = ?
                ''', (rating, comment, now, message_id))
            else:
                cursor.execute('''
                    INSERT INTO feedback (feedback_id, message_id, session_id, rating, comment, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (feedback_id, message_id, session_id, rating, comment, now))
            conn.commit()
        logger.info(f"成功保存/更新消息反馈 (Message ID: {message_id}, 评级: {rating})")
        
        # 联动触发质量重估，本地导入避免循环依赖
        try:
            from services.quality_service import QualityService
            qs = QualityService()
            qs.reevaluate_on_feedback(message_id, rating)
        except Exception as qe:
            logger.error(f"反馈联动触发质量评估重算失败: {qe}")
            
        return True
    except sqlite3.Error as e:
        logger.error(f"保存反馈失败: {e}")
        return False

def get_feedback_by_message_id(message_id: str) -> Optional[Dict[str, Any]]:
    """
    根据 message_id 获取反馈。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM feedback WHERE message_id = ?', (message_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"获取反馈失败: {e}")
        return None

# --- 其他清理接口 ---

def delete_message_sources_by_doc_id(doc_id: str) -> bool:
    """
    删除与指定 doc_id 关联的所有引用来源记录。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM message_sources WHERE doc_id = ?', (doc_id,))
            conn.commit()
        logger.info(f"成功从 message_sources 中清理文档 {doc_id} 的关联引用")
        return True
    except sqlite3.Error as e:
        logger.error(f"清理 message_sources 关联记录失败: {e}")
        return False


# --- Tool Logs (工具日志) 操作 ---

def save_tool_log(
    tool_name: str,
    tool_display_name: str,
    tool_args: str,
    tool_result: str,
    success: int,
    elapsed_ms: int,
    session_id: Optional[str] = None,
    message_id: Optional[str] = None,
    error_message: Optional[str] = None
) -> str:
    """
    记录一次工具调用到 SQLite 中。返回 tool_log_id。
    """
    tool_log_id = str(uuid.uuid4())
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tool_logs (
                    tool_log_id, session_id, message_id, tool_name, tool_display_name,
                    tool_args, tool_result, success, error_message, elapsed_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tool_log_id, session_id, message_id, tool_name, tool_display_name,
                tool_args, tool_result, success, error_message, elapsed_ms, now
            ))
            conn.commit()
        return tool_log_id
    except sqlite3.Error as e:
        logger.error(f"保存工具日志失败: {e}")
        return ""

def list_tool_logs(limit: int = 100, tool_name: Optional[str] = None, success: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    获取工具调用日志列表。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM tool_logs WHERE 1=1"
            params = []
            if tool_name:
                query += " AND tool_name = ?"
                params.append(tool_name)
            if success is not None:
                query += " AND success = ?"
                params.append(success)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error(f"查询工具日志失败: {e}")
        return []


# --- Agent Traces (执行轨迹) 操作 ---

def save_agent_trace(
    session_id: Optional[str],
    message_id: Optional[str],
    step_index: int,
    step_type: str,
    step_title: str,
    step_detail: str
) -> str:
    """
    记录一次 Agent 运行步骤轨迹。返回 trace_id。
    """
    trace_id = str(uuid.uuid4())
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO agent_traces (
                    trace_id, session_id, message_id, step_index, step_type, step_title, step_detail, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trace_id, session_id, message_id, step_index, step_type, step_title, step_detail, now))
            conn.commit()
        return trace_id
    except sqlite3.Error as e:
        logger.error(f"保存 Agent 轨迹失败: {e}")
        return ""

def get_agent_traces(session_id: str, message_id: str) -> List[Dict[str, Any]]:
    """
    查询某次消息/会话的 Agent 执行轨迹，按步骤正序。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM agent_traces 
                WHERE session_id = ? AND message_id = ? 
                ORDER BY step_index ASC
            ''', (session_id, message_id))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error(f"查询 Agent 轨迹失败: {e}")
        return []


# --- Quality Evaluations (质量评估) 操作 ---

def save_quality_evaluation(
    message_id: str,
    session_id: str,
    score: int,
    is_low_quality: int,
    issues: str,
    suggestion: str,
    evaluator: str = "rules"
) -> str:
    """
    保存回答的质量评估记录。并同步更新 messages 表中该消息的 quality_score 和 is_low_quality 字段。
    """
    evaluation_id = str(uuid.uuid4())
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 写入 quality_evaluations
            cursor.execute('''
                INSERT INTO quality_evaluations (
                    evaluation_id, message_id, session_id, score, is_low_quality, issues, suggestion, evaluator, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (evaluation_id, message_id, session_id, score, is_low_quality, issues, suggestion, evaluator, now))
            
            # 2. 联动更新 messages 中的字段
            cursor.execute('''
                UPDATE messages 
                SET quality_score = ?, is_low_quality = ? 
                WHERE message_id = ?
            ''', (score, is_low_quality, message_id))
            
            conn.commit()
        return evaluation_id
    except sqlite3.Error as e:
        logger.error(f"保存质量评估记录失败: {e}")
        return ""

def list_quality_evaluations(
    limit: int = 100, 
    is_low_quality: Optional[int] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    查询质量评估列表（带筛选，关联查询消息表中的原始提问和回复）。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    q.evaluation_id,
                    q.message_id,
                    q.session_id,
                    q.score,
                    q.is_low_quality,
                    q.issues,
                    q.suggestion,
                    q.evaluator,
                    q.created_at,
                    m_ast.content as assistant_answer,
                    m_ast.intent_name,
                    m_usr.content as user_question,
                    f.rating as feedback_rating,
                    f.comment as feedback_comment
                FROM quality_evaluations q
                JOIN messages m_ast ON q.message_id = m_ast.message_id
                LEFT JOIN messages m_usr ON m_usr.rowid = (
                    SELECT MAX(rowid) FROM messages 
                    WHERE session_id = m_ast.session_id 
                      AND role = 'user' 
                      AND rowid < m_ast.rowid
                )
                LEFT JOIN feedback f ON q.message_id = f.message_id
                WHERE 1=1
            """
            params = []
            if is_low_quality is not None:
                query += " AND q.is_low_quality = ?"
                params.append(is_low_quality)
            if min_score is not None:
                query += " AND q.score >= ?"
                params.append(min_score)
            if max_score is not None:
                query += " AND q.score <= ?"
                params.append(max_score)
                
            query += " ORDER BY q.created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error(f"查询质量评估列表失败: {e}")
        return []

def update_message_quality_fields(message_id: str, score: int, is_low_quality: int) -> bool:
    """
    直接更新 messages 字段的辅助接口。
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE messages 
                SET quality_score = ?, is_low_quality = ? 
                WHERE message_id = ?
            ''', (score, is_low_quality, message_id))
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"直接更新消息质量属性失败: {e}")
        return False
