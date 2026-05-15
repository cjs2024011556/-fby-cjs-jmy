"""管理台数据模型"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from motoengine.models.chatmodel import AgentMetadata


class SessionListItem(BaseModel):
    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    chat_count: int = Field(default=0, description="消息数量")


class ChatRecord(BaseModel):
    chat_id: str = Field(..., description="聊天ID")
    question: str = Field(..., description="问题")
    answer: str = Field(..., description="回答")
    metadata: AgentMetadata = Field(default_factory=lambda: AgentMetadata(source="rag", reasoning=""))
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    completed: bool = Field(default=False, description="是否完成")


class SessionDetail(BaseModel):
    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    chats: List[ChatRecord] = Field(default_factory=list, description="聊天列表")


class SessionCreateRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="会话ID，不传则自动生成")
    title: Optional[str] = Field(None, description="会话标题")


class SessionUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, description="会话标题")


class ChatCreateRequest(BaseModel):
    question: str = Field(..., description="问题")
    answer: str = Field(default="", description="回答")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    completed: bool = Field(default=False, description="是否完成")


class ChatUpdateRequest(BaseModel):
    question: Optional[str] = Field(None, description="问题")
    answer: Optional[str] = Field(None, description="回答")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    completed: Optional[bool] = Field(None, description="是否完成")


class AdminOverviewResponse(BaseModel):
    session_count: int = Field(..., description="会话总数")
    chat_count: int = Field(..., description="聊天总数")
    vector_chunks: int = Field(..., description="向量块总数")
    vector_chapters: Dict[str, int] = Field(default_factory=dict, description="章节分布")
    manual_loaded: bool = Field(default=False, description="手册是否已加载")
