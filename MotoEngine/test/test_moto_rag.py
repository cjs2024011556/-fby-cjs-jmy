"""测试脚本 - RAG 检索模块"""

import asyncio

from motoengine.func.moto_rag import RAGRetriever


async def test_stream_query(retriever: RAGRetriever, question: str):
    """异步流式测试"""
    print("流式回答：")
    full_answer = ""
    async for chunk in retriever.query_stream_async(question):
        print(chunk, end="", flush=True)
        full_answer += chunk
    print(f"\n\n完整答案长度：{len(full_answer)} 字符")


def main():
    """主函数：测试 RAG 检索"""
    print("=" * 60)
    print("摩托车发动机维修手册 - RAG 检索测试")
    print("=" * 60)

    print("\n初始化 RAG 检索器...")
    retriever = RAGRetriever()
    print("✓ RAG 检索器初始化完成")

    question1 = "火花塞的间隙是多少？"
    print(f"\n【问题 1】{question1}")
    print("-" * 40)

    try:
        result = retriever.query(question1)
        print(f"答案：{result['answer']}")
        print(f"参考文档数：{len(result['source_documents'])}")
    except Exception as e:
        print(f"❌ 查询失败：{e}")

    question2 = "发动机机油如何更换？"
    print(f"\n【问题 2】{question2}")
    print("-" * 40)

    try:
        asyncio.run(test_stream_query(retriever, question2))
    except Exception as e:
        print(f"❌ 流式查询失败：{e}")

    print("\n" + "=" * 60)
    print("✓ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
