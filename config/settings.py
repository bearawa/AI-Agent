import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 阿里百炼 API 密钥与基础配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 模型配置
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen-plus")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")

# 存储路径转换为绝对路径
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma_db")
if not os.path.isabs(CHROMA_DIR):
    CHROMA_DIR = str((BASE_DIR / CHROMA_DIR).resolve())

SQLITE_PATH = os.getenv("SQLITE_PATH", "data/campus_service.db")
if not os.path.isabs(SQLITE_PATH):
    SQLITE_PATH = str((BASE_DIR / SQLITE_PATH).resolve())

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/raw_documents")
if not os.path.isabs(UPLOAD_DIR):
    UPLOAD_DIR = str((BASE_DIR / UPLOAD_DIR).resolve())

# 创建这些本地存储目录
os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(str(BASE_DIR / "logs"), exist_ok=True)

# RAG 参数
try:
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
except ValueError:
    RAG_TOP_K = 5

try:
    threshold_str = os.getenv("RAG_DISTANCE_THRESHOLD", "")
    RAG_DISTANCE_THRESHOLD = float(threshold_str) if threshold_str else 0.8
except ValueError:
    RAG_DISTANCE_THRESHOLD = 0.8

try:
    MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "6"))
except ValueError:
    MAX_HISTORY_MESSAGES = 6

# 项目名称
PROJECT_NAME = os.getenv("PROJECT_NAME", "AIZS")
PROJECT_FULL_NAME = os.getenv("PROJECT_FULL_NAME", "AIZS｜校园智能咨询平台")

# 管理员认证
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = str((BASE_DIR / "logs" / "app.log").resolve())
