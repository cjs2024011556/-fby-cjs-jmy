"""SSE事件相关的数据模型 - 通用模板设计"""

from typing import Optional

from pydantic import BaseModel, Field

from motoengine.models.chatmodel import AgentMetadata


class SSEBaseEvent(BaseModel):
    """SSE事件基类"""

    event_type: str = Field(..., description="事件类型")
    data: dict = Field(..., description="事件数据")


class SSEMetadataEvent(BaseModel):
    """SSE Metadata事件 - 包含chat_id、session_id和Agent判断的metadata"""

    chat_id: str = Field(..., description="聊天ID")
    session_id: str = Field(..., description="会话ID")
    metadata: AgentMetadata = Field(..., description="Agent判断的详细metadata")


class SSEMessageEvent(BaseModel):
    """SSE Message事件 - 包含文本chunk"""

    chunk: str = Field(..., description="文本片段")
    done: bool = Field(default=False, description="是否完成")
    chat_id: Optional[str] = Field(None, description="聊天ID（仅在第一个chunk中包含）")
    session_id: Optional[str] = Field(
        None, description="会话ID（仅在第一个chunk中包含）"
    )
    metadata: Optional[AgentMetadata] = Field(
        None, description="Agent判断的metadata（仅在第一个chunk中包含）"
    )


class SSEDoneEvent(BaseModel):
    """SSE Done事件 - 表示流式输出完成"""

    chat_id: str = Field(..., description="聊天ID")
    session_id: str = Field(..., description="会话ID")
    done: bool = Field(default=True, description="是否完成")


class SSEErrorEvent(BaseModel):
    """SSE Error事件 - 表示发生错误"""

    chat_id: Optional[str] = Field(None, description="聊天ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    error: str = Field(..., description="错误信息")
    done: bool = Field(default=True, description="是否完成")


class SSEEventResponse(BaseModel):
    """SSE事件响应 - 统一的响应格式"""

    event: str = Field(..., description="事件类型：metadata, message, done, error")
    data: dict = Field(..., description="事件数据（字典格式）")

    def to_sse_format(self) -> dict:
        import json

        return {
            "event": self.event,
            "data": json.dumps(self.data, ensure_ascii=False),
        }

    @classmethod
    def from_metadata(cls, metadata_event: SSEMetadataEvent) -> "SSEEventResponse":
        return cls(
            event="metadata",
            data=metadata_event.model_dump(),
        )

    @classmethod
    def from_message(cls, message_event: SSEMessageEvent) -> "SSEEventResponse":
        return cls(
            event="message",
            data=message_event.model_dump(),
        )

    @classmethod
    def from_done(cls, done_event: SSEDoneEvent) -> "SSEEventResponse":
        return cls(
            event="done",
            data=done_event.model_dump(),
        )

    @classmethod
    def from_error(cls, error_event: SSEErrorEvent) -> "SSEEventResponse":
        return cls(
            event="error",
            data=error_event.model_dump(),
        )
