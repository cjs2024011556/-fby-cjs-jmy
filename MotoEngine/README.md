# MotoEngine

MotoEngine 是一个基于 FastAPI 的项目骨架。

## 目录结构

- `motoengine/`：核心 Python 包
- `motoengine/func/`：核心功能模块
- `motoengine/route/`：FastAPI 路由层
- `data/vector_db/`：向量库存储目录
- `uploads/`：用户上传文件目录

## 启动

```bash
python -m motoengine
```

API:

- `GET /api/health`
- `POST /api/chat`
