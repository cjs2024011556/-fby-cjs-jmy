"""文档向量化模块 - 使用阿里云百炼 Embedding 模型"""

from typing import List

from langchain.embeddings.base import Embeddings
from openai import OpenAI

from motoengine.utils.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, EMBEDDING_MODEL, require_dashscope_api_key


class AliyunEmbeddings(Embeddings):
    """阿里云百炼嵌入模型类，继承自 LangChain 的 Embeddings 基类"""

    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
    ):
        self.model = model or EMBEDDING_MODEL
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.base_url = base_url or DASHSCOPE_BASE_URL
        self.client = None

    def _get_client(self) -> OpenAI:
        if self.client is None:
            self.client = OpenAI(
                api_key=self.api_key or require_dashscope_api_key(),
                base_url=self.base_url,
            )
        return self.client

    def embed_query(self, text: str) -> List[float]:
        response = self._get_client().embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self._get_client().embeddings.create(model=self.model, input=texts)
        return [embedding.embedding for embedding in response.data]


embedding_model = AliyunEmbeddings()
