#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AIZS 演示数据重置脚本
用于重置系统数据，清除已导入的文档、对话历史和向量库数据，回到系统初始状态。
支持参数：
  --yes, -y        跳过二次确认提示
  --keep-logs      保留审计与评估日志（不清除 feedback, tool_logs, agent_traces, quality_evaluations 状态）
"""

import os
import sys
import argparse
import shutil
import sqlite3
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 解决 Windows 命令行下打印 Emoji 的编码问题
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config import settings
from repositories.sqlite_repository import init_db, get_connection
from repositories.chroma_repository import ChromaRepository
from utils.logger import logger

def clear_directory_contents(dir_path):
    """清空目录下的所有文件和子目录，但保留目录本身"""
    path = Path(dir_path)
    if not path.exists():
        os.makedirs(path, exist_ok=True)
        return
    for item in path.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            print(f"清空 {item} 时出错: {e}")

def reset_data(yes=False, keep_logs=False):
    # 确认提示
    if not yes:
        confirm = input("⚠️  警告：此操作将清空系统的演示数据！是否确定继续？(y/N): ")
        if confirm.lower() != 'y':
            print("操作已取消。")
            return

    print("开始重置 AIZS 演示数据...")

    # 1. 处理 Chroma 向量数据库
    print("正在清空 Chroma 向量数据库...")
    if keep_logs:
        # 如果保留日志，我们通过获取 documents 表中的所有 doc_id 来逐个删除向量
        try:
            chroma_repo = ChromaRepository()
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT doc_id, file_name FROM documents")
                docs = cursor.fetchall()
                for doc in docs:
                    doc_id = doc[0]
                    file_name = doc[1]
                    print(f"  正在删除文档向量: {file_name} ({doc_id})")
                    chroma_repo.delete_by_doc_id(doc_id)
        except Exception as e:
            print(f"清空向量数据失败 (keep-logs 模式): {e}")
    else:
        # 如果不保留日志，直接删除整个 Chroma 目录
        chroma_dir = Path(settings.CHROMA_DIR)
        if chroma_dir.exists():
            try:
                shutil.rmtree(chroma_dir)
                print("  已删除 Chroma 数据目录")
            except Exception as e:
                print(f"  删除 Chroma 数据目录失败: {e}，尝试清空集合...")
                try:
                    chroma_repo = ChromaRepository()
                    chroma_repo.client.delete_collection(chroma_repo.collection_name)
                except Exception as ex:
                    print(f"  清空集合也失败: {ex}")
        else:
            print("  Chroma 数据目录不存在，无需清理")

    # 2. 处理 raw_documents (上传的文件)
    print("正在清空已上传的原始文档目录...")
    clear_directory_contents(settings.UPLOAD_DIR)
    print("  已清空 raw_documents 目录")

    # 3. 处理 SQLite 数据库
    print("正在重置 SQLite 数据库...")
    if keep_logs:
        # 保留日志，只清除业务相关的表
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                # 关闭外键约束以防删除报错
                cursor.execute("PRAGMA foreign_keys = OFF;")
                
                print("  正在清除 documents 表...")
                cursor.execute("DELETE FROM documents;")
                
                print("  正在清除 chat_sessions 表...")
                cursor.execute("DELETE FROM chat_sessions;")
                
                print("  正在清除 messages 表...")
                cursor.execute("DELETE FROM messages;")
                
                print("  正在清除 message_sources 表...")
                cursor.execute("DELETE FROM message_sources;")
                
                # 重新开启外键
                cursor.execute("PRAGMA foreign_keys = ON;")
                conn.commit()
            print("  业务数据表清理完毕 (日志与审计表已保留)")
        except sqlite3.Error as e:
            print(f"清理业务表失败: {e}")
            sys.exit(1)
    else:
        # 不保留日志，直接物理删除数据库文件并重新建表
        sqlite_path = Path(settings.SQLITE_PATH)
        if sqlite_path.exists():
            try:
                # 直接删除文件
                sqlite_path.unlink()
                print("  已删除 SQLite 数据库文件")
            except Exception as e:
                print(f"  直接删除数据库文件失败: {e}，尝试执行 TRUNCATE TABLE...")
                try:
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("PRAGMA foreign_keys = OFF;")
                        tables = ["documents", "chat_sessions", "messages", "message_sources", "feedback", "tool_logs", "agent_traces", "quality_evaluations"]
                        for table in tables:
                            cursor.execute(f"DELETE FROM {table};")
                        cursor.execute("PRAGMA foreign_keys = ON;")
                        conn.commit()
                    print("  所有数据表已清空")
                except Exception as ex:
                    print(f"  清空数据表也失败: {ex}")
                    sys.exit(1)
        
        # 重新建表
        print("  正在重新初始化数据库表结构...")
        init_db()
        print("  SQLite 数据库重新初始化完成")

    print("🎉 AIZS 演示数据重置成功！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIZS 演示数据重置脚本")
    parser.add_argument("-y", "--yes", action="store_true", help="跳过二次确认提示")
    parser.add_argument("--keep-logs", action="store_true", help="保留审计与评估日志")
    args = parser.parse_args()
    
    reset_data(yes=args.yes, keep_logs=args.keep_logs)
