"""数据库管理路由"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Path

from motoengine.func.chat_storage import ChatStorage
from motoengine.func.document_vector import DocumentEmbedder
from motoengine.func.chat_memory import MemoryManager
from motoengine.models.admin import (
    AdminOverviewResponse,
    ChatCreateRequest,
    ChatRecord,
    ChatUpdateRequest,
    SessionCreateRequest,
    SessionDetail,
    SessionListItem,
    SessionUpdateRequest,
)
from motoengine.models.chatmodel import AgentMetadata
from motoengine.utils.config import MANUAL_FILE

router = APIRouter(prefix="/api/v2/admin", tags=["admin"])

chat_storage = ChatStorage()


def _metadata_from_dict(payload: dict | None) -> AgentMetadata:
    payload = payload or {}
    return AgentMetadata(
        source=payload.get("source", "rag"),
        reasoning=payload.get("reasoning", ""),
        workflow_type=payload.get("workflow_type"),
        chapter_id=payload.get("chapter_id"),
        chapter_name=payload.get("chapter_name"),
    )


def _chat_to_model(chat: dict) -> ChatRecord:
    return ChatRecord(
        chat_id=chat["chat_id"],
        question=chat.get("question", ""),
        answer=chat.get("answer", ""),
        metadata=_metadata_from_dict(chat.get("metadata")),
        created_at=chat.get("created_at", datetime.now().isoformat()),
        updated_at=chat.get("updated_at", datetime.now().isoformat()),
        completed=chat.get("completed", False),
    )


@router.get("/overview", response_model=AdminOverviewResponse)
async def get_overview() -> AdminOverviewResponse:
    storage_sessions = chat_storage.list_sessions()
    session_count = len(storage_sessions)
    chat_count = sum(item.get("chat_count", 0) for item in storage_sessions)

    embedder = DocumentEmbedder()
    vector_info = embedder.get_collection_info()

    return AdminOverviewResponse(
        session_count=session_count,
        chat_count=chat_count,
        vector_chunks=vector_info.get("total_chunks", 0),
        vector_chapters=vector_info.get("chapter_counts", {}),
        manual_loaded=MANUAL_FILE.exists(),
    )


@router.get("/sessions")
async def list_sessions():
    return {"sessions": chat_storage.list_sessions()}


@router.post("/sessions", response_model=SessionDetail)
async def create_session(payload: SessionCreateRequest) -> SessionDetail:
    session_id = payload.session_id or str(uuid.uuid4())
    existing = chat_storage.get_session(session_id)
    if existing:
        raise HTTPException(status_code=409, detail="会话已存在")

    session = chat_storage.create_session(session_id, title=payload.title)
    return SessionDetail(
        session_id=session["session_id"],
        title=session.get("title", "新会话"),
        created_at=session.get("created_at"),
        updated_at=session.get("updated_at"),
        chats=[],
    )


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str = Path(..., description="会话ID"),
) -> SessionDetail:
    session = chat_storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return SessionDetail(
        session_id=session["session_id"],
        title=session.get("title", "新会话"),
        created_at=session.get("created_at"),
        updated_at=session.get("updated_at"),
        chats=[_chat_to_model(chat) for chat in session.get("chats", [])],
    )


@router.put("/sessions/{session_id}", response_model=SessionDetail)
async def update_session(
    session_id: str = Path(..., description="会话ID"),
    payload: SessionUpdateRequest = ...,
) -> SessionDetail:
    session = chat_storage.update_session(session_id, title=payload.title)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return SessionDetail(
        session_id=session["session_id"],
        title=session.get("title", "新会话"),
        created_at=session.get("created_at"),
        updated_at=session.get("updated_at"),
        chats=[_chat_to_model(chat) for chat in session.get("chats", [])],
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str = Path(..., description="会话ID"),
):
    deleted = chat_storage.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    MemoryManager(session_id=session_id).clear_all()
    try:
        from motoengine.route.chat_router import _agent_cache

        _agent_cache.pop(session_id, None)
    except Exception:
        pass
    return {"session_id": session_id, "deleted": True}


@router.get("/sessions/{session_id}/chats")
async def list_chats(
    session_id: str = Path(..., description="会话ID"),
):
    session = chat_storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {"chats": [_chat_to_model(chat).model_dump() for chat in session.get("chats", [])]}


@router.post("/sessions/{session_id}/chats", response_model=ChatRecord)
async def create_chat(
    session_id: str = Path(..., description="会话ID"),
    payload: ChatCreateRequest = ...,
) -> ChatRecord:
    session = chat_storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    chat_id = str(uuid.uuid4())
    chat_storage.create_chat(
        session_id=session_id,
        chat_id=chat_id,
        question=payload.question,
        metadata=payload.metadata,
    )
    if payload.answer or payload.completed:
        chat_storage.update_chat(
            session_id=session_id,
            chat_id=chat_id,
            answer=payload.answer if payload.answer else None,
            replace_answer=True,
            completed=payload.completed,
        )
    chat = chat_storage.get_chat(session_id, chat_id)
    if not chat:
        raise HTTPException(status_code=500, detail="聊天记录创建失败")
    return _chat_to_model(chat)


@router.get("/sessions/{session_id}/chats/{chat_id}", response_model=ChatRecord)
async def get_chat(
    session_id: str = Path(..., description="会话ID"),
    chat_id: str = Path(..., description="聊天ID"),
) -> ChatRecord:
    chat = chat_storage.get_chat(session_id, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="聊天记录不存在")
    return _chat_to_model(chat)


@router.put("/sessions/{session_id}/chats/{chat_id}", response_model=ChatRecord)
async def update_chat(
    session_id: str = Path(..., description="会话ID"),
    chat_id: str = Path(..., description="聊天ID"),
    payload: ChatUpdateRequest = ...,
) -> ChatRecord:
    chat = chat_storage.update_chat(
        session_id=session_id,
        chat_id=chat_id,
        question=payload.question,
        answer=payload.answer,
        replace_answer=True,
        metadata=payload.metadata,
        completed=payload.completed,
    )
    if not chat:
        raise HTTPException(status_code=404, detail="聊天记录不存在")
    return _chat_to_model(chat)


@router.delete("/sessions/{session_id}/chats/{chat_id}")
async def delete_chat(
    session_id: str = Path(..., description="会话ID"),
    chat_id: str = Path(..., description="聊天ID"),
):
    deleted = chat_storage.delete_chat(session_id, chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="聊天记录不存在")
    return {"session_id": session_id, "chat_id": chat_id, "deleted": True}
