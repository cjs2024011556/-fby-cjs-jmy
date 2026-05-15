"""Workflow 模块 - 基于章节的 RAG 工作流"""

from typing import Optional

from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate

from motoengine.func.chat_memory import MemoryManager
from motoengine.func.document_vector import DocumentEmbedder
from motoengine.func.streaming_llm import get_llm

EMPTY_ANSWER_NOTICE = (
    "当前没有加载到可用的维修手册内容，暂时无法基于该章节给出准确回答。"
    "请先确认 `docs/摩托车发动机维修手册.md` 已下载并完成向量化。"
)


class ChapterWorkflow:
    """章节工作流 - 基于具体章节的 RAG 对话"""

    def __init__(
        self,
        chapter_id: str,
        chapter_name: str,
        embedder: Optional[DocumentEmbedder] = None,
        memory_manager: Optional[MemoryManager] = None,
        session_id: str = "default",
    ):
        self.chapter_id = chapter_id
        self.chapter_name = chapter_name
        self.embedder = embedder or DocumentEmbedder()
        if self.embedder.vectorstore is None:
            self.embedder.load_or_create_vectorstore()
        self.embedder.bootstrap_from_sources()

        self.memory_manager = memory_manager or MemoryManager(session_id)
        self.session_id = session_id
        self.llm = get_llm()

        self.retriever = self.embedder.vectorstore.as_retriever(
            search_kwargs={"k": 5, "filter": {"chapter_id": chapter_id}}
        )

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
        )
        self._load_history()

        self.qa_prompt = PromptTemplate(
            template=f"""你是一位专业的摩托车发动机维修专家，正在指导用户进行"{chapter_name}"部件的维修工作。

请基于维修手册中关于"{chapter_name}"的内容，一步步指导用户完成维修任务。

维修手册内容：
{{context}}

用户问题：{{question}}

请提供：
1. 清晰、详细的步骤说明
2. 必要的注意事项和警告
3. 如果用户已完成某一步，确认并引导进入下一步
4. 如果用户遇到问题，提供解决方案

回答：""",
            input_variables=["context", "question"],
        )

        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt},
            return_source_documents=True,
            verbose=False,
        )

    def _load_history(self):
        history = self.memory_manager.get_workflow_history(self.chapter_id)
        for msg in history.messages:
            if hasattr(msg, "content"):
                msg_class_name = msg.__class__.__name__
                if "Human" in msg_class_name:
                    self.memory.chat_memory.add_user_message(msg.content)
                elif "AI" in msg_class_name:
                    self.memory.chat_memory.add_ai_message(msg.content)

    def _save_history(self, question: str, answer: str):
        history = self.memory_manager.get_workflow_history(self.chapter_id)
        history.add_user_message(question)
        history.add_ai_message(answer)

    def process(self, question: str) -> dict:
        result = self.qa_chain.invoke({"question": question})

        answer = (result.get("answer", "") or "").strip()
        if not answer:
            answer = EMPTY_ANSWER_NOTICE
        source_documents = result.get("source_documents", [])

        self._save_history(question, answer)

        return {
            "answer": answer,
            "source_documents": source_documents,
            "chapter_id": self.chapter_id,
            "chapter_name": self.chapter_name,
        }

    async def process_stream_async(self, question: str):
        docs = self.retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])
        if not context.strip():
            notice = EMPTY_ANSWER_NOTICE
            self._save_history(question, notice)
            yield notice
            return

        chat_history = self.memory.chat_memory.messages
        history_text = ""
        for msg in chat_history:
            if hasattr(msg, "content"):
                role = "用户" if "Human" in msg.__class__.__name__ else "助手"
                history_text += f"{role}: {msg.content}\n"

        prompt = self.qa_prompt.format(
            context=context,
            question=question,
        )

        if history_text:
            prompt = f"对话历史：\n{history_text}\n\n{prompt}"

        from motoengine.func.streaming_llm import astream_dashscope

        full_answer = ""
        async for chunk in astream_dashscope(prompt, temperature=0.7):
            if chunk:
                yield chunk
                full_answer += chunk

        if not full_answer.strip():
            full_answer = EMPTY_ANSWER_NOTICE
            yield full_answer

        self._save_history(question, full_answer)

    def process_stream(self, question: str):
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        async_gen = self.process_stream_async(question)
        while True:
            try:
                chunk = loop.run_until_complete(async_gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break

    def clear_history(self):
        self.memory.clear()
        self.memory_manager.clear_workflow_history(self.chapter_id)
