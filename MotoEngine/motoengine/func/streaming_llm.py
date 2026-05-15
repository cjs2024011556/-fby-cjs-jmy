"""直接使用官方 OpenAI SDK 对接阿里云百炼（极简版）"""

from typing import AsyncIterator

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI

from motoengine.utils.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, LLM_MODEL


def _build_async_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL)


def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    """获取 LLM 实例"""
    return ChatOpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
        model=LLM_MODEL,
        temperature=temperature,
        streaming=True,
    )


async def astream_dashscope(
    prompt: str, temperature: float = 0.7
) -> AsyncIterator[str]:
    """官方原生流式实现"""
    completion = await _build_async_client().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=True,
        stream_options={"include_usage": True},
        temperature=temperature,
    )

    async for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
