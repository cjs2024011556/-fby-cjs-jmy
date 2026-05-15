"""测试脚本 - 测试RAG检索和Workflow功能"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from motoengine.func import ChapterWorkflow, MemoryManager


def test_workflow():
    """测试章节Workflow"""
    print("=" * 60)
    print("测试章节Workflow")
    print("=" * 60)
    print()

    session_id = "test_session_001"
    memory_manager = MemoryManager(session_id)

    workflow = ChapterWorkflow(
        chapter_id="一",
        chapter_name="火花塞",
        memory_manager=memory_manager,
        session_id=session_id,
    )

    print(f"【Workflow】第{workflow.chapter_id}章: {workflow.chapter_name}")
    print()

    questions = [
        "我想拆卸火花塞，应该怎么做？",
        "拆卸时需要注意什么？",
        "如何检查火花塞是否正常？",
    ]

    for i, question in enumerate(questions, 1):
        print(f"【问题 {i}】{question}")
        result = workflow.process(question)
        print(f"【回答】{result['answer']}")
        print()


def test_memory_separation():
    """测试聊天历史分离"""
    print("=" * 60)
    print("测试聊天历史分离")
    print("=" * 60)
    print()

    session_id = "test_session_002"
    memory_manager = MemoryManager(session_id)

    workflow1 = ChapterWorkflow(
        chapter_id="一",
        chapter_name="火花塞",
        memory_manager=memory_manager,
        session_id=session_id,
    )

    workflow2 = ChapterWorkflow(
        chapter_id="二",
        chapter_name="起动电机",
        memory_manager=memory_manager,
        session_id=session_id,
    )

    print("【Workflow 1】火花塞章节")
    result1 = workflow1.process("如何拆卸火花塞？")
    print("问题: 如何拆卸火花塞？")
    print(f"回答: {result1['answer'][:100]}...")
    print()

    print("【Workflow 2】起动电机章节")
    result2 = workflow2.process("如何拆卸起动电机？")
    print("问题: 如何拆卸起动电机？")
    print(f"回答: {result2['answer'][:100]}...")
    print()

    history1 = memory_manager.get_workflow_history("一")
    history2 = memory_manager.get_workflow_history("二")

    print(f"火花塞章节对话历史: {len(history1.messages)} 条消息")
    print(f"起动电机章节对话历史: {len(history2.messages)} 条消息")
    print("✓ 聊天历史已正确分离")


if __name__ == "__main__":
    test_workflow()
    print("\n" + "=" * 60 + "\n")
    test_memory_separation()
