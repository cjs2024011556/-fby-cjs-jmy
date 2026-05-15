"""RAG检索模块 - 基于向量数据库的检索增强生成"""

from typing import Optional

from langchain_classic.chains import RetrievalQA
from langchain_classic.chains.retrieval_qa.base import BaseRetrievalQA
from langchain_core.prompts import PromptTemplate

from motoengine.func.document_vector import DocumentEmbedder
from motoengine.func.streaming_llm import astream_dashscope, get_llm

EMPTY_ANSWER_NOTICE = (
    "当前没有加载到可用的维修手册内容，暂时无法基于手册给出准确回答。"
    "请先确认 `docs/摩托车发动机维修手册.md` 已下载并完成向量化。"
)


class RAGRetriever:
    """RAG检索器"""

    def __init__(self, embedder: Optional[DocumentEmbedder] = None):
        self.embedder = embedder or DocumentEmbedder()
        if self.embedder.vectorstore is None:
            self.embedder.load_or_create_vectorstore()
        self.embedder.bootstrap_from_sources()

        self.llm = get_llm()

        self.qa_prompt = PromptTemplate(
            template="""你是一位专业的摩托车发动机维修专家助手。请基于以下维修手册内容回答用户的问题。
如果问题涉及具体的维修步骤，请按照手册中的步骤详细说明。
如果问题涉及技术参数，请准确引用手册中的数据。
如果手册中没有相关信息，请诚实告知用户。
维修手册内容：
{context}
问题：{question}
请提供专业、准确、详细的回答：""",
            input_variables=["context", "question"],
        )

        self.qa_chain: Optional[BaseRetrievalQA] = None
        self._create_qa_chain()

    def _create_qa_chain(self, filter_dict: Optional[dict] = None):
        retriever = self.embedder.vectorstore.as_retriever(
            search_kwargs={"k": 5}
        )

        if filter_dict:
            retriever = self.embedder.vectorstore.as_retriever(
                search_kwargs={"k": 5, "filter": filter_dict}
            )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": self.qa_prompt},
            return_source_documents=True,
        )

    def query(self, question: str, chapter_id: Optional[str] = None) -> dict:
        if chapter_id:
            self._create_qa_chain(filter_dict={"chapter_id": chapter_id})
        elif self.qa_chain is None:
            self._create_qa_chain()

        result = self.qa_chain.invoke({"query": question})

        answer = (result.get("result", "") or "").strip()
        if not answer:
            answer = EMPTY_ANSWER_NOTICE
        source_documents = result.get("source_documents", [])

        return {
            "answer": answer,
            "source_documents": source_documents,
        }

    async def query_stream_async(self, question: str, chapter_id: Optional[str] = None):
        if chapter_id:
            retriever = self.embedder.vectorstore.as_retriever(
                search_kwargs={"k": 5, "filter": {"chapter_id": chapter_id}}
            )
        else:
            retriever = self.embedder.vectorstore.as_retriever(search_kwargs={"k": 5})

        docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])
        if not context.strip():
            yield EMPTY_ANSWER_NOTICE
            return

        prompt = self.qa_prompt.format(context=context, question=question)

        has_chunk = False
        async for chunk in astream_dashscope(prompt, temperature=0.7):
            if chunk:
                has_chunk = True
                yield chunk

        if not has_chunk:
            yield EMPTY_ANSWER_NOTICE

    def query_stream(self, question: str, chapter_id: Optional[str] = None):
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        async_gen = self.query_stream_async(question, chapter_id)
        while True:
            try:
                chunk = loop.run_until_complete(async_gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break
