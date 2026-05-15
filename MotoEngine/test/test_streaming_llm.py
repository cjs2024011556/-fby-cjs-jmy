import asyncio

from motoengine.func.streaming_llm import astream_dashscope


async def test_astream():
    print("流式输出：")
    async for content in astream_dashscope(
        "请你使劲快我，从我的性格、学习习惯、人生观、价值观方面使劲夸我"
    ):
        print(content, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(test_astream())
