"""测试脚本 - MotoAgent 模块"""

import asyncio

from motoengine.func.moto_agent import RepairAgent


async def test_stream_process(agent: RepairAgent, question: str):
    """异步流式测试"""
    full_answer = ""
    async for chunk in agent.process_stream_async(question):
        print(chunk, end="", flush=True)
        full_answer += chunk
    print(f"\n\n完整答案长度：{len(full_answer)} 字符")
    return full_answer


def main():
    """主函数：测试 MotoAgent 模块"""
    print("=" * 60)
    print("摩托车发动机维修智能体测试")
    print("=" * 60)

    session_id = "test_agent_session"
    print(f"\n会话 ID: {session_id}")

    print("\n初始化 RepairAgent...")
    agent = RepairAgent(session_id=session_id)
    print("✓ RepairAgent 初始化完成")

    print("\n可用章节:")
    for chapter_id, chapter_name in agent.chapters.items():
        print(f"  - 第{chapter_id}章：{chapter_name}")

    question1 = "摩托车发动机保养需要注意什么？"
    print(f"\n【问题 1】{question1}")
    print("-" * 40)

    try:
        result = agent.process(question1)
        print(f"答案：{result['answer'][:300]}...")
        print(f"来源：{result['source']}")
        print(f"元数据：{result['metadata']['reasoning']}")
    except Exception as e:
        print(f"❌ 查询失败：{e}")

    question2 = "如何拆卸火花塞？"
    print(f"\n【问题 2】{question2}")
    print("-" * 40)

    try:
        result = agent.process(question2)
        print(f"答案：{result['answer'][:300]}...")
        print(f"来源：{result['source']}")
        print(f"章节：{result.get('chapter_id')} - {result.get('chapter_name')}")
    except Exception as e:
        print(f"❌ 查询失败：{e}")

    question3 = "火花塞的间隙标准值是多少？"
    print(f"\n【问题 3】{question3}（流式）")
    print("-" * 40)

    try:
        asyncio.run(test_stream_process(agent, question3))
    except Exception as e:
        print(f"❌ 流式查询失败：{e}")

    question4 = "起动电机如何维修？"
    print(f"\n【问题 4】{question4}（切换 Workflow）")
    print("-" * 40)

    try:
        result = agent.process(question4)
        print(f"答案：{result['answer'][:300]}...")
        print(f"来源：{result['source']}")
        print(f"章节：{result.get('chapter_id')} - {result.get('chapter_name')}")
    except Exception as e:
        print(f"❌ 查询失败：{e}")

    print("\n【测试 5】获取活跃 Workflow")
    print("-" * 40)
    active = agent.get_active_workflows()
    if active:
        print("活跃 Workflow:")
        for cid, cname in active.items():
            print(f"  - 第{cid}章：{cname}")
    else:
        print("当前无活跃 Workflow")

    print("\n【测试 6】清空 Workflow")
    print("-" * 40)
    for chapter_id in list(agent.active_workflows.keys()):
        agent.clear_workflow(chapter_id)
        print(f"✓ 已清空第{chapter_id}章 Workflow")

    print("\n" + "=" * 60)
    print("✓ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
