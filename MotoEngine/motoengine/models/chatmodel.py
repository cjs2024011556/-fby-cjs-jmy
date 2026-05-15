"""聊天相关的数据模型"""
from typing import List, Optional

from pydantic import BaseModel, Field


class AgentMetadata(BaseModel):
    """Agent判断的详细metadata"""

    source: str = Field(..., description="来源：rag 或 workflow")
    reasoning: str = Field(..., description="判断理由")
    workflow_type: Optional[str] = Field(
        None, description="工作流类型：chapter_workflow, active_workflow等"
    )
    chapter_id: Optional[str] = Field(None, description="章节ID（如果使用Workflow）")
    chapter_name: Optional[str] = Field(None, description="章节名称（如果使用Workflow）")


class SessionResponse(BaseModel):
    """会话响应模型"""

    session_id: str = Field(..., description="会话ID")
    created_at: Optional[str] = Field(None, description="创建时间")


class CreateMessageRequest(BaseModel):
    """创建消息请求模型"""

    question: str = Field(..., description="用户问题")


class CreateMessageResponse(BaseModel):
    """创建消息响应模型"""

    chat_id: str = Field(..., description="聊天ID")
    session_id: str = Field(..., description="会话ID")
    metadata: AgentMetadata = Field(..., description="Agent判断的metadata")


class ChatStreamResponse(BaseModel):
    """流式响应模型"""

    chunk: str = Field(..., description="文本片段")
    done: bool = Field(default=False, description="是否完成")
    chat_id: Optional[str] = Field(None, description="聊天ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    metadata: Optional[AgentMetadata] = Field(None, description="Agent判断的metadata")


class ChatHistoryItem(BaseModel):
    """聊天历史项"""

    chat_id: str = Field(..., description="聊天ID")
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="回答内容")
    metadata: AgentMetadata = Field(..., description="Agent判断的metadata")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    completed: bool = Field(..., description="是否完成")


class SessionHistoryResponse(BaseModel):
    """会话历史响应模型"""

    session_id: str = Field(..., description="会话ID")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    chats: List[ChatHistoryItem] = Field(default_factory=list, description="聊天记录列表")


class WorkflowSummaryRequest(BaseModel):
    """Workflow摘要请求模型"""

    session_id: str = Field(..., description="会话ID")
    chapter_id: Optional[str] = Field(
        None, description="章节ID，如果为None则返回所有活跃Workflow的摘要"
    )


class WorkflowSummaryResponse(BaseModel):
    """Workflow摘要响应模型"""

    summary: str = Field(..., description="摘要内容")
    session_id: str = Field(..., description="会话ID")
