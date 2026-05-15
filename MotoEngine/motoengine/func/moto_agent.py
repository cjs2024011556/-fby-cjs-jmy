"""Agent 模块 - 统领整个维修流程的智能体"""

from __future__ import annotations

import json
import re
from typing import Dict, Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage

from motoengine.func.chat_memory import MemoryManager
from motoengine.func.document_vector import DocumentEmbedder
from motoengine.func.manual_splitter import ManualSplitter
from motoengine.func.moto_rag import RAGRetriever
from motoengine.func.streaming_llm import get_llm
from motoengine.func.workflow import ChapterWorkflow

EMPTY_ANSWER_NOTICE = (
    "当前没有加载到可用的维修手册内容，暂时无法给出基于手册的准确回答。"
    "请先确认 `docs/摩托车发动机维修手册.md` 已下载并完成向量化。"
)


class RepairAgent:
    """维修智能体 - 统领整个维修流程"""

    def __init__(
        self,
        session_id: str = "default",
        embedder: Optional[DocumentEmbedder] = None,
        memory_manager: Optional[MemoryManager] = None,
    ):
        self.session_id = session_id
        self.embedder = embedder or DocumentEmbedder()
        self.memory_manager = memory_manager or MemoryManager(session_id)

        self.rag_retriever = RAGRetriever(embedder=self.embedder)

        self.chapters: Dict[str, str] = {}
        self.chapters_info: Dict[str, Dict] = {}
        try:
            splitter = ManualSplitter()
            chapters = splitter.split_by_chapters()
            self.chapters = {
                chapter["chapter_id"]: chapter["chapter_name"] for chapter in chapters
            }
            self.chapters_info = {
                chapter["chapter_id"]: {
                    "name": chapter["chapter_name"],
                    "number": chapter["chapter_number"],
                    "sections": [
                        {"id": s["id"], "name": s["name"]}
                        for s in chapter.get("sections", [])
                    ],
                }
                for chapter in chapters
            }
        except FileNotFoundError:
            # 手册未下载时允许系统先启动，后续走兜底回答。
            self.chapters = {}
            self.chapters_info = {}

        self.active_workflows: Dict[str, ChapterWorkflow] = {}
        self.llm = get_llm()
        self.system_prompt = (
            "你是一位专业的摩托车发动机维修智能助手，负责统领整个维修流程。\n\n"
            "你的职责：\n"
            "1. 理解用户的维修需求（意图识别）\n"
            "2. 判断是否需要进入具体部件的维修流程（Workflow）\n"
            "3. 如果需要，指定对应的章节Workflow\n"
            "4. 如果不需要，使用RAG检索回答\n\n"
            f"可用的维修章节：\n{self._format_chapters_info()}\n\n"
            "判断规则：\n"
            "- 如果用户明确提到某个部件，或者需要详细的步骤指导，应该进入对应章节的Workflow\n"
            "- 如果只是询问一般性问题、参数，或需要快速回答，可以直接使用RAG检索\n"
            "- 如果用户提到的是不同的部件，应该切换到新的Workflow；如果用户问的是通用问题，应该退出Workflow使用RAG\n\n"
            "请严格只返回以下 JSON，不要输出其他文字：\n"
            '{\n'
            '  "use_workflow": true/false,\n'
            '  "chapter_id": "章节ID（如\'一\'，如果 use_workflow 为 false 则为 null）",\n'
            '  "reasoning": "判断理由"\n'
            "}\n"
        )

    def _format_chapters_info(self) -> str:
        if not self.chapters_info:
            return "暂无可用章节"

        lines = []
        for chapter_id, info in self.chapters_info.items():
            sections = "、".join(
                f"{section['id']} {section['name']}" for section in info["sections"]
            )
            if not sections:
                sections = "无子章节"
            lines.append(f"第{chapter_id}章: {info['name']}\n  子章节: {sections}")
        return "\n".join(lines)

    def _get_or_create_workflow(self, chapter_id: str) -> ChapterWorkflow:
        if chapter_id not in self.active_workflows:
            chapter_name = self.chapters.get(chapter_id, "未知")
            self.active_workflows[chapter_id] = ChapterWorkflow(
                chapter_id=chapter_id,
                chapter_name=chapter_name,
                embedder=self.embedder,
                memory_manager=self.memory_manager,
                session_id=self.session_id,
            )
        return self.active_workflows[chapter_id]

    def _detect_chapter_simple(self, question: str) -> Optional[str]:
        for chapter_id, chapter_name in self.chapters.items():
            if chapter_name and chapter_name in question:
                return chapter_id
        return None

    @staticmethod
    def get_fallback_answer(question: str = "") -> str:
        if question.strip():
            return f"{EMPTY_ANSWER_NOTICE}\n\n当前问题：{question}"
        return EMPTY_ANSWER_NOTICE

    def _parse_decision(self, response_text: str) -> Optional[dict]:
        if not response_text:
            return None

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        code_block_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL
        )
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except json.JSONDecodeError:
                pass

        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _should_use_workflow(self, question: str) -> Tuple[bool, Optional[str], Dict]:
        metadata = {
            "source": "rag",
            "reasoning": "",
            "workflow_type": None,
        }

        if not self.chapters:
            metadata["reasoning"] = "手册章节未加载，使用 RAG 兜底"
            return False, None, metadata

        active_chapter_id = next(iter(self.active_workflows), None)

        try:
            agent_history = self.memory_manager.get_agent_history()
            history_messages = agent_history.messages[-6:]

            messages = [SystemMessage(content=self.system_prompt)]
            messages.extend(history_messages)

            current_context = ""
            if active_chapter_id:
                current_context = (
                    f"\n\n当前活跃的Workflow：第{active_chapter_id}章 - "
                    f"{self.chapters.get(active_chapter_id, '未知')}\n"
                    "注意：如果用户提到其他部件，应该切换到新的Workflow；"
                    "如果用户问通用问题，应该退出Workflow使用RAG。"
                )

            messages.append(
                HumanMessage(
                    content=(
                        f"用户问题：{question}{current_context}\n\n"
                        "请判断应该使用RAG还是Workflow，并返回 JSON。"
                    )
                )
            )

            response = self.llm.invoke(messages)
            response_text = str(getattr(response, "content", "") or "").strip()
            print(f"[Agent意图识别] LLM响应: {response_text}")

            decision = self._parse_decision(response_text)
            if not decision:
                chapter_id = self._detect_chapter_simple(question)
                if chapter_id:
                    decision = {
                        "use_workflow": True,
                        "chapter_id": chapter_id,
                        "reasoning": f"关键词匹配到章节 {self.chapters.get(chapter_id, '未知')}",
                    }
                else:
                    decision = {
                        "use_workflow": False,
                        "chapter_id": None,
                        "reasoning": "无法解析 LLM 响应，使用 RAG",
                    }

            use_workflow = bool(decision.get("use_workflow", False))
            chapter_id = decision.get("chapter_id")
            reasoning = decision.get("reasoning", "")

            if use_workflow and chapter_id:
                chapter_id_str = str(chapter_id).strip()
                if chapter_id_str not in self.chapters:
                    for cid, cname in self.chapters.items():
                        if chapter_id_str == cname or chapter_id_str in cname or cname in chapter_id_str:
                            chapter_id_str = cid
                            break

                if chapter_id_str in self.chapters:
                    metadata.update(
                        {
                            "source": "workflow",
                            "reasoning": reasoning or "LLM 判断需要进入章节工作流",
                            "workflow_type": "chapter_workflow",
                            "chapter_id": chapter_id_str,
                            "chapter_name": self.chapters.get(chapter_id_str, "未知"),
                        }
                    )
                    return True, chapter_id_str, metadata

                metadata["reasoning"] = (
                    f"LLM 返回的章节ID '{chapter_id_str}' 无效，使用 RAG 检索"
                )
                return False, None, metadata

            if active_chapter_id:
                metadata["reasoning"] = reasoning or "用户问的是通用问题，退出 Workflow 使用 RAG"
            else:
                metadata["reasoning"] = reasoning or "LLM 判断使用 RAG 检索"
            return False, None, metadata

        except Exception as exc:
            print(f"警告: LLM 意图识别失败: {exc}，使用后备逻辑")
            chapter_id = self._detect_chapter_simple(question)
            if chapter_id:
                metadata.update(
                    {
                        "reasoning": f"检测到章节 '{self.chapters.get(chapter_id, '未知')}'，使用后备逻辑进入 Workflow",
                        "chapter_id": chapter_id,
                        "chapter_name": self.chapters.get(chapter_id, "未知"),
                        "source": "workflow",
                        "workflow_type": "chapter_workflow",
                    }
                )
                return True, chapter_id, metadata

            metadata["reasoning"] = "意图识别失败，使用 RAG 检索通用知识"
            return False, None, metadata

    def decide_route(self, question: str) -> Tuple[bool, Optional[str], Dict]:
        """公开的路由决策入口。"""
        return self._should_use_workflow(question)

    def process(
        self,
        question: str,
        decision: Optional[Tuple[bool, Optional[str], Dict]] = None,
    ) -> dict:
        agent_history = self.memory_manager.get_agent_history()
        agent_history.add_user_message(question)

        use_workflow, chapter_id, metadata = decision or self._should_use_workflow(question)

        if use_workflow and chapter_id:
            if self.active_workflows:
                old_chapter_id = next(iter(self.active_workflows), None)
                if old_chapter_id and old_chapter_id != chapter_id:
                    self.active_workflows.pop(old_chapter_id, None)
        elif not use_workflow:
            self.active_workflows.clear()

        if use_workflow and chapter_id:
            workflow = self._get_or_create_workflow(chapter_id)
            result = workflow.process(question)
            answer = (result.get("answer") or "").strip() or self.get_fallback_answer(question)
            agent_history.add_ai_message(f"[Workflow-{chapter_id}] {answer}")
            return {
                "answer": answer,
                "source": "workflow",
                "chapter_id": chapter_id,
                "chapter_name": self.chapters.get(chapter_id, "未知"),
                "source_documents": result.get("source_documents", []),
                "metadata": metadata,
            }

        result = self.rag_retriever.query(question)
        answer = (result.get("answer") or "").strip() or self.get_fallback_answer(question)
        agent_history.add_ai_message(f"[RAG] {answer}")
        return {
            "answer": answer,
            "source": "rag",
            "chapter_id": None,
            "chapter_name": None,
            "source_documents": result.get("source_documents", []),
            "metadata": metadata,
        }

    async def process_stream_async(
        self,
        question: str,
        decision: Optional[Tuple[bool, Optional[str], Dict]] = None,
    ):
        agent_history = self.memory_manager.get_agent_history()
        agent_history.add_user_message(question)

        use_workflow, chapter_id, metadata = decision or self._should_use_workflow(question)

        if use_workflow and chapter_id:
            if self.active_workflows:
                old_chapter_id = next(iter(self.active_workflows), None)
                if old_chapter_id and old_chapter_id != chapter_id:
                    self.active_workflows.pop(old_chapter_id, None)
        elif not use_workflow:
            self.active_workflows.clear()

        full_answer = ""
        if use_workflow and chapter_id:
            workflow = self._get_or_create_workflow(chapter_id)
            async for chunk in workflow.process_stream_async(question):
                if chunk:
                    full_answer += chunk
                    yield chunk
        else:
            async for chunk in self.rag_retriever.query_stream_async(question):
                if chunk:
                    full_answer += chunk
                    yield chunk

        if not full_answer.strip():
            full_answer = self.get_fallback_answer(question)
            yield full_answer

        source_tag = f"Workflow-{chapter_id}" if (use_workflow and chapter_id) else "RAG"
        agent_history.add_ai_message(f"[{source_tag}] {full_answer}")

    def get_active_workflows(self) -> Dict[str, str]:
        return {
            chapter_id: self.chapters.get(chapter_id, "未知")
            for chapter_id in self.active_workflows
        }

    def clear_workflow(self, chapter_id: str):
        workflow = self.active_workflows.get(chapter_id)
        if workflow is not None:
            workflow.clear_history()
        self.active_workflows.pop(chapter_id, None)
