"""聊天相关的 API 路由 - BS 架构设计"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi import Path as PathParam
from sse_starlette.sse import EventSourceResponse

from motoengine.func import MemoryManager, RepairAgent
from motoengine.func.chat_storage import ChatStorage
from motoengine.models.chatmodel import (
    AgentMetadata,
    ChatHistoryItem,
    CreateMessageRequest,
    SessionHistoryResponse,
    SessionResponse,
)
from motoengine.models.sse import (
    SSEDoneEvent,
    SSEErrorEvent,
    SSEEventResponse,
    SSEMessageEvent,
    SSEMetadataEvent,
)

router = APIRouter(prefix="/api/v2/chat", tags=["chat"])

_agent_cache: dict[str, RepairAgent] = {}
chat_storage = ChatStorage()


def get_or_create_agent(session_id: str) -> RepairAgent:
    if session_id not in _agent_cache:
        memory_manager = MemoryManager(session_id=session_id)
        _agent_cache[session_id] = RepairAgent(
            session_id=session_id, memory_manager=memory_manager
        )
    return _agent_cache[session_id]


def _clear_agent_session(session_id: str) -> None:
    agent = _agent_cache.pop(session_id, None)
    MemoryManager(session_id=session_id).clear_all()
    if agent is not None:
        agent.active_workflows.clear()


@router.get("/session", response_model=SessionResponse)
async def create_session() -> SessionResponse:
    session_id = str(uuid.uuid4())
    chat_storage.create_session(session_id)
    get_or_create_agent(session_id)

    return SessionResponse(
        session_id=session_id,
        created_at=datetime.now().isoformat(),
    )


@router.get("/sessions")
async def list_sessions():
    """获取所有会话列表"""
    return {"sessions": chat_storage.list_sessions()}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str = PathParam(..., description="会话ID")):
    """删除一个会话"""
    deleted = chat_storage.delete_session(session_id)
    _clear_agent_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"session_id": session_id, "deleted": True}


@router.post("/{session_id}/messages")
async def create_message(
    session_id: str = PathParam(..., description="会话ID"),
    request: CreateMessageRequest = ...,
) -> EventSourceResponse:
    session_data = chat_storage.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")

    chat_id = str(uuid.uuid4())
    agent = get_or_create_agent(session_id)
    decision = agent.decide_route(request.question)
    _, _, metadata_dict = decision
    metadata = AgentMetadata(**metadata_dict)

    chat_storage.create_chat(
        session_id=session_id,
        chat_id=chat_id,
        question=request.question,
        metadata=metadata.model_dump(),
    )

    async def event_generator():
        try:
            metadata_event = SSEMetadataEvent(
                chat_id=chat_id,
                session_id=session_id,
                metadata=metadata,
            )
            yield SSEEventResponse.from_metadata(metadata_event).to_sse_format()

            first_chunk = True

            async for chunk in agent.process_stream_async(request.question, decision=decision):
                if chunk:
                    message_event = SSEMessageEvent(
                        chunk=chunk,
                        done=False,
                        chat_id=chat_id if first_chunk else None,
                        session_id=session_id if first_chunk else None,
                        metadata=metadata if first_chunk else None,
                    )
                    yield SSEEventResponse.from_message(message_event).to_sse_format()
                    first_chunk = False

                    chat_storage.update_chat(
                        session_id=session_id,
                        chat_id=chat_id,
                        answer=chunk,
                    )

            chat_storage.update_chat(
                session_id=session_id,
                chat_id=chat_id,
                completed=True,
            )

            done_event = SSEDoneEvent(
                chat_id=chat_id,
                session_id=session_id,
            )
            yield SSEEventResponse.from_done(done_event).to_sse_format()
        except Exception as e:
            chat_storage.update_chat(
                session_id=session_id,
                chat_id=chat_id,
                completed=True,
            )
            error_event = SSEErrorEvent(
                chat_id=chat_id,
                session_id=session_id,
                error=str(e),
            )
            yield SSEEventResponse.from_error(error_event).to_sse_format()

    return EventSourceResponse(event_generator())


@router.get("/{session_id}/messages", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str = PathParam(..., description="会话ID"),
) -> SessionHistoryResponse:
    session_data = chat_storage.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")

    chats = []
    for chat_data in session_data.get("chats", []):
        chats.append(
            ChatHistoryItem(
                chat_id=chat_data["chat_id"],
                question=chat_data["question"],
                answer=chat_data.get("answer", ""),
                metadata=AgentMetadata(**chat_data.get("metadata", {})),
                created_at=chat_data["created_at"],
                updated_at=chat_data["updated_at"],
                completed=chat_data.get("completed", False),
            )
        )

    return SessionHistoryResponse(
        session_id=session_id,
        created_at=session_data.get("created_at"),
        updated_at=session_data.get("updated_at"),
        chats=chats,
    )


@router.get("/chapters")
async def get_chapters():
    """获取所有可用章节列表"""
    try:
        agent = get_or_create_agent("default")
        chapters = {
            chapter_id: {
                "name": info["name"],
                "number": info["number"],
                "sections": info["sections"],
            }
            for chapter_id, info in agent.chapters_info.items()
        }
        return {"chapters": chapters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取章节列表时出错: {str(e)}")
