"""配置管理模块"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 目录配置
DOCS_DIR = PROJECT_ROOT / "docs"
DB_DIR = PROJECT_ROOT / "db"
CHROMA_DIR = DB_DIR / "chroma"
CHAT_HISTORY_DIR = DB_DIR / "chat_history"
CHAPTERS_DIR = DOCS_DIR / "chapters"

# 确保目录存在
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

# API配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_MODEL = "qwen-plus"

# Embedding配置
EMBEDDING_MODEL = "text-embedding-v2"

# ChromaDB配置
CHROMA_COLLECTION_NAME = "motorcycle_repair_manual"
CHROMA_PERSIST_DIRECTORY = str(CHROMA_DIR)

# 文档配置
MANUAL_FILE = DOCS_DIR / "摩托车发动机维修手册.md"


def require_dashscope_api_key() -> str:
    """获取必需的 DashScope API Key。"""
    if not DASHSCOPE_API_KEY:
        raise ValueError("请在 .env 文件中设置 DASHSCOPE_API_KEY")
    return DASHSCOPE_API_KEY
