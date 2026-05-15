"""聊天存储模块 - 本地 JSON 持久化"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from motoengine.utils.config import CHAT_HISTORY_DIR


class ChatStorage:
    """简单的本地聊天存储。"""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or CHAT_HISTORY_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.storage_dir / f"{session_id}.json"

    def _write_session(self, session_id: str, data: Dict[str, Any]) -> None:
        path = self._session_path(session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def create_session(self, session_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        data = self.get_session(session_id)
        now = datetime.now().isoformat()
        if data:
            if title is not None:
                data["title"] = title
                data["updated_at"] = now
                self._write_session(session_id, data)
            return data

        data = {
            "session_id": session_id,
            "title": title or "新会话",
            "created_at": now,
            "updated_at": now,
            "chats": [],
        }
        self._write_session(session_id, data)
        return data

    def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        session = self.get_session(session_id)
        if not session:
            return None

        if title is not None:
            session["title"] = title
        session["updated_at"] = datetime.now().isoformat()
        self._write_session(session_id, session)
        return session

    def delete_session(self, session_id: str) -> bool:
        path = self._session_path(session_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def list_sessions(self) -> list[Dict[str, Any]]:
        sessions: list[Dict[str, Any]] = []
        files = sorted(
            self.storage_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in files:
            data = self.get_session(path.stem)
            if not data:
                continue
            sessions.append(
                {
                    "session_id": data.get("session_id", path.stem),
                    "title": data.get("title", "新会话"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "chat_count": len(data.get("chats", [])),
                }
            )
        return sessions

    def create_chat(
        self,
        session_id: str,
        chat_id: str,
        question: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        session = self.get_session(session_id) or self.create_session(session_id)
        now = datetime.now().isoformat()
        chat = {
            "chat_id": chat_id,
            "question": question,
            "answer": "",
            "metadata": metadata,
            "created_at": now,
            "updated_at": now,
            "completed": False,
        }
        session.setdefault("chats", []).append(chat)
        session["updated_at"] = now
        self._write_session(session_id, session)
        return chat

    def list_chats(self, session_id: str) -> list[Dict[str, Any]]:
        session = self.get_session(session_id)
        if not session:
            return []
        return list(session.get("chats", []))

    def get_chat(self, session_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        session = self.get_session(session_id)
        if not session:
            return None
        for chat in session.get("chats", []):
            if chat.get("chat_id") == chat_id:
                return chat
        return None

    def update_chat(
        self,
        session_id: str,
        chat_id: str,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        replace_answer: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        completed: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        session = self.get_session(session_id)
        if not session:
            return None

        now = datetime.now().isoformat()
        for chat in session.get("chats", []):
            if chat.get("chat_id") == chat_id:
                if question is not None:
                    chat["question"] = question
                if answer is not None:
                    if replace_answer:
                        chat["answer"] = answer
                    else:
                        chat["answer"] = chat.get("answer", "") + answer
                if metadata is not None:
                    chat["metadata"] = metadata
                if completed is not None:
                    chat["completed"] = completed
                chat["updated_at"] = now
                session["updated_at"] = now
                self._write_session(session_id, session)
                return chat
        return None

    def delete_chat(self, session_id: str, chat_id: str) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False

        chats = session.get("chats", [])
        new_chats = [chat for chat in chats if chat.get("chat_id") != chat_id]
        if len(new_chats) == len(chats):
            return False

        session["chats"] = new_chats
        session["updated_at"] = datetime.now().isoformat()
        self._write_session(session_id, session)
        return True
