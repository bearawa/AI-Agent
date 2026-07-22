from contextlib import asynccontextmanager
import json
import logging
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import settings
from repositories import sqlite_repository
from services.chat_service import ChatService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 在应用启动时初始化数据库
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("Initializing SQLite database on startup...")
    try:
        sqlite_repository.init_db()
    except Exception as e:
        logger.error(f"Failed to initialize SQLite database: {e}")
    yield
    # 关闭时执行 (可以留空)

app = FastAPI(title="AIZS API", description="AIZS FastAPI Backend for Next.js Frontend", lifespan=lifespan)

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应配置为具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
chat_service = ChatService()

# --- Pydantic 模型 ---
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

class SessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str

class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    content: str
    created_at: str

# --- API 路由 ---

@app.post("/api/admin/login")
def admin_login(req: AdminLoginRequest):
    expected_user = settings.ADMIN_USERNAME
    expected_pass = settings.ADMIN_PASSWORD

    if not expected_user or not expected_pass:
        raise HTTPException(status_code=500, detail="Admin credentials not configured")

    if req.username == expected_user and req.password == expected_pass:
        return {"status": "success", "message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.get("/api/admin/status")
def admin_status():
    try:
        sessions_count = len(sqlite_repository.list_chat_sessions())
        return {
            "status": "online",
            "total_sessions": sessions_count,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

@app.get("/api/sessions", response_model=List[SessionResponse])
def list_sessions():
    """获取所有会话列表"""
    sessions = sqlite_repository.list_chat_sessions()
    return sessions

@app.post("/api/sessions", response_model=dict)
def create_session():
    """创建一个新会话"""
    try:
        new_id = chat_service.start_new_session()
        return {"session_id": new_id}
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    """获取指定会话详情"""
    sessions = sqlite_repository.list_chat_sessions()
    for s in sessions:
        if s["session_id"] == session_id:
            return s
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/api/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_messages(session_id: str):
    """获取指定会话的历史消息"""
    try:
        messages = sqlite_repository.get_chat_messages(session_id)
        return messages
    except Exception as e:
        logger.error(f"Failed to get messages for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
def chat_stream(req: ChatMessageRequest):
    """流式返回大模型的回答"""

    def generate():
        try:
            # 1. 记录用户输入的消息，获取内部生成的 message_id (如果 chat_service.handle_chat_flow 需要，但它目前处理逻辑在内部)
            # 在目前的架构中，handle_chat_flow 会在生成回答的同时保存消息。

            stream = chat_service.handle_chat_flow(req.session_id, req.message)

            for chunk in stream:
                # 将内部的字典转换为 JSON 字符串并作为 SSE (Server-Sent Events) 发送
                data_str = json.dumps(chunk, ensure_ascii=False)
                yield f"data: {data_str}\n\n"

        except Exception as e:
            logger.error(f"Error in chat_stream: {e}")
            error_data = json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
