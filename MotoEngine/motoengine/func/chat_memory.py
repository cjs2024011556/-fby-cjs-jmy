"""聊天历史管理模块 - 分离Agent和Workflow的聊天历史"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from motoengine.utils.config import CHAT_HISTORY_DIR


class FileChatMessageHistory(BaseChatMessageHistory):
    """基于文件的聊天历史存储"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.messages: List[BaseMessage] = []
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.messages = self._deserialize_messages(data.get("messages", []))
            except Exception as e:
                print(f"警告: 加载聊天历史失败: {e}")
                self.messages = []

    def _save(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "messages": self._serialize_messages(self.messages),
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"警告: 保存聊天历史失败: {e}")

    def _serialize_messages(self, messages: List[BaseMessage]) -> List[dict]:
        result = []
        for msg in messages:
            result.append({"type": msg.__class__.__name__, "content": msg.content})
        return result

    def _deserialize_messages(self, data: List[dict]) -> List[BaseMessage]:
        messages = []
        for item in data:
            msg_type = item.get("type")
            content = item.get("content", "")
            if msg_type == "HumanMessage":
                messages.append(HumanMessage(content=content))
            elif msg_type == "AIMessage":
                messages.append(AIMessage(content=content))
        return messages

    @property
    def messages(self) -> List[BaseMessage]:
        return self._messages

    @messages.setter
    def messages(self, value: List[BaseMessage]):
        self._messages = value

    def add_message(self, message: BaseMessage):
        self.messages.append(message)
        self._save()

    def add_user_message(self, message: str):
        self.add_message(HumanMessage(content=message))

    def add_ai_message(self, message: str):
        self.add_message(AIMessage(content=message))

    def clear(self):
        self.messages = []
        self._save()


class MemoryManager:
    """聊天历史管理器"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = CHAT_HISTORY_DIR / session_id
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_agent_history(self) -> FileChatMessageHistory:
        file_path = self.base_dir / "agent_history.json"
        return FileChatMessageHistory(file_path)

    def get_workflow_history(self, chapter_id: str) -> FileChatMessageHistory:
        file_path = self.base_dir / f"workflow_{chapter_id}_history.json"
        return FileChatMessageHistory(file_path)

    def clear_agent_history(self):
        history = self.get_agent_history()
        history.clear()

    def clear_workflow_history(self, chapter_id: str):
        history = self.get_workflow_history(chapter_id)
        history.clear()

    def clear_all(self):
        self.clear_agent_history()
        for file_path in self.base_dir.glob("workflow_*_history.json"):
            history = FileChatMessageHistory(file_path)
            history.clear()
