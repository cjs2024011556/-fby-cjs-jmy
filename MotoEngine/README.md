# MotoEngine

MotoEngine 是一个基于 FastAPI 的摩托车维修助手项目。

## 目录结构

- `motoengine/`：项目主包
- `motoengine/func/`：核心功能模块
- `motoengine/route/`：FastAPI 路由层
- `data/vector_db/`：向量库持久化目录
- `uploads/`：用户上传文件目录

## 配置模块

项目的基础配置主要位于 `motoengine/utils/config.py`，负责环境变量加载、路径定义和核心服务参数初始化。

### 1. 基础依赖与环境加载

```python
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
```

- `os` 用于读取环境变量。
- `Path` 用于跨平台路径拼接。
- `load_dotenv()` 会自动读取项目中的 `.env` 文件，并将其中的键值对注入到当前进程环境中。

### 2. 路径配置

```python
PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
DB_DIR = PROJECT_ROOT / "db"
CHROMA_DIR = DB_DIR / "chroma"
CHAT_HISTORY_DIR = DB_DIR / "chat_history"
CHAPTERS_DIR = DOCS_DIR / "chapters"
```

- `PROJECT_ROOT` 会自动定位到项目根目录。
- 使用 `/` 拼接路径比字符串拼接更安全，也更适合跨平台。
- 这些目录会在启动时自动创建，避免第一次运行时报目录不存在的错误。

### 3. 核心服务配置

```python
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("请在 .env 文件中设置 DASHSCOPE_API_KEY")

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_MODEL = "qwen-plus"
EMBEDDING_MODEL = "text-embedding-v2"
```

- `DASHSCOPE_API_KEY` 从环境变量读取，如果没有配置会直接报错。
- `DASHSCOPE_BASE_URL` 是 DashScope 的 OpenAI 兼容接口地址。
- `LLM_MODEL` 默认使用 `qwen-plus`。
- `EMBEDDING_MODEL` 默认使用 `text-embedding-v2`。

### 4. 应用特定配置

```python
CHROMA_COLLECTION_NAME = "motorcycle_repair_manual"
CHROMA_PERSIST_DIRECTORY = str(CHROMA_DIR)
MANUAL_FILE = DOCS_DIR / "摩托车发动机维修手册.md"
```

- `CHROMA_COLLECTION_NAME` 是向量数据库中的集合名称。
- `CHROMA_PERSIST_DIRECTORY` 指向 ChromaDB 的持久化目录。
- `MANUAL_FILE` 指向项目使用的原始维修手册文档。

## 启动

```bash
python -m motoengine
```

## API

- `GET /api/health`
- `POST /api/chat`
