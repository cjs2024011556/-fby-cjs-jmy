# MotoEngine

MotoEngine 是一个基于 `FastAPI + ChromaDB + DashScope` 的摩托车发动机维修智能体项目。当前版本已经包含手册切分、向量检索、章节 Workflow、Agent 路由、SSE 流式输出、会话历史持久化，以及独立的数据库可视化与 CRUD 管理台。

## 项目结构

```text
MotoEngine/
├── motoengine/
│   ├── __main__.py            # 主入口，挂载 /agent /manual /admin
│   ├── func/                  # 核心业务逻辑
│   │   ├── manual_splitter.py # 手册按章节切分
│   │   ├── document_vector.py # 切分、向量化、检索
│   │   ├── moto_rag.py        # RAG 检索
│   │   ├── workflow.py        # 章节级工作流
│   │   ├── moto_agent.py      # 总控 Agent
│   │   ├── chat_storage.py    # 聊天 JSON 存储
│   │   └── chat_memory.py     # Workflow 历史存储
│   ├── models/                # Pydantic 数据模型
│   ├── route/                 # API 路由
│   │   ├── chat_router.py     # 聊天 / SSE / 会话
│   │   └── admin_router.py    # 数据库可视化 CRUD
│   ├── templates/             # 独立前端页面
│   │   ├── agent/             # 智能体工作台
│   │   ├── admin/             # 数据库管理台
│   │   └── manual/            # 手册页面
│   └── utils/config.py        # 路径、模型、环境变量
├── docs/                      # 手册正文与图片资源
├── db/                        # Chroma 与聊天历史
└── test/                      # 模块测试入口
```

## 架构图

```mermaid
flowchart LR
  U[浏览器] --> A[/templates/agent/]
  U --> D[/templates/admin/]
  A --> R[/api/v2/chat]
  D --> M[/api/v2/admin]
  R --> AG[moto_agent.py]
  AG --> RAG[moto_rag.py]
  AG --> WF[workflow.py]
  RAG --> V[document_vector.py]
  WF --> H[chat_memory.py]
  M --> S[chat_storage.py]
  V --> C[(ChromaDB)]
  S --> J[(本地 JSON)]
```

## 功能概览

- 手册切分：`motoengine/func/manual_splitter.py`
- 向量化检索：`motoengine/func/document_vector.py`
- 通用问答：`motoengine/func/moto_rag.py`
- 章节工作流：`motoengine/func/workflow.py`
- 总控路由：`motoengine/func/moto_agent.py`
- 聊天历史：`motoengine/func/chat_storage.py`、`motoengine/func/chat_memory.py`
- 独立前端：
  - `http://localhost:8000/agent/` 智能体工作台
  - `http://localhost:8000/admin/` 数据库管理台
  - `http://localhost:8000/manual/` 手册页面

## 数据管理台

`/admin/` 是独立页面，支持：

- 会话列表查看
- 新建 / 删除会话
- 修改会话标题
- 查看聊天记录
- 新增 / 编辑 / 删除单条聊天
- 查看向量库概览与手册加载状态

对应接口位于：

- `motoengine/route/admin_router.py`
- `motoengine/func/chat_storage.py`

## 主要接口

- `GET /api-docs`
- `GET /api/health`
- `GET /api/v2/chat/session`
- `GET /api/v2/chat/sessions`
- `DELETE /api/v2/chat/session/{session_id}`
- `POST /api/v2/chat/{session_id}/messages`
- `GET /api/v2/chat/{session_id}/messages`
- `GET /api/v2/chat/chapters`
- `GET /api/v2/admin/overview`
- `GET/POST/PUT/DELETE /api/v2/admin/sessions...`
- `GET/POST/PUT/DELETE /api/v2/admin/sessions/{session_id}/chats...`

## 启动方式

```bash
python -m motoengine
```

启动后可访问：

- `http://localhost:8000/` 首页
- `http://localhost:8000/agent/` 智能体工作台
- `http://localhost:8000/admin/` 数据库管理台
- `http://localhost:8000/api-docs` API 文档

## 环境说明

- 需要在 `.env` 中配置 `DASHSCOPE_API_KEY`
- 向量库与聊天历史默认落在 `db/`
- 手册正文默认读取 `docs/摩托车发动机维修手册.md`

## 本次新增

- 新增独立数据库管理台 `/admin/`
- 新增会话 / 聊天 CRUD 接口
- 新增向量库概览信息
- 整理首页入口，补充 `/agent/`、`/admin/`、`/manual/`
