"""测试脚本 - 聊天历史管理模块"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from motoengine.func.chat_memory import MemoryManager


def main():
    """主函数：测试聊天历史管理"""
    print("=" * 60)
    print("聊天历史管理模块测试")
    print("=" * 60)

    session_id = "test_session_001"
    print(f"\n测试会话：{session_id}")

    print("\n初始化 MemoryManager...")
    memory = MemoryManager(session_id)
    print("✓ MemoryManager 初始化完成")

    print("\n【测试 1】Agent 聊天历史")
    print("-" * 40)
    agent_history = memory.get_agent_history()

    print("添加消息...")
    agent_history.add_user_message("你好，发动机如何保养？")
    agent_history.add_ai_message("您好！发动机保养需要定期检查机油、空滤和火花塞。")
    agent_history.add_user_message("机油多久更换一次？")
    agent_history.add_ai_message("建议每 3000-5000 公里更换一次机油。")

    print(f"\n当前消息数：{len(agent_history.messages)}")
    print("消息列表:")
    for i, msg in enumerate(agent_history.messages, 1):
        print(f"  {i}. [{msg.__class__.__name__}] {msg.content[:50]}...")

    print("\n【测试 2】Workflow 聊天历史（章节：一）")
    print("-" * 40)
    workflow_history = memory.get_workflow_history("一")

    print("添加消息...")
    workflow_history.add_user_message("火花塞间隙是多少？")
    workflow_history.add_ai_message("标准火花塞间隙为 0.6-0.7mm。")

    print(f"\n当前消息数：{len(workflow_history.messages)}")
    print("消息列表:")
    for i, msg in enumerate(workflow_history.messages, 1):
        print(f"  {i}. [{msg.__class__.__name__}] {msg.content}")

    print("\n【测试 3】清空聊天历史")
    print("-" * 40)
    print("清空 Agent 历史...")
    memory.clear_agent_history()
    print(f"清空后 Agent 消息数：{len(memory.get_agent_history().messages)}")

    print("\n清空所有历史...")
    memory.clear_all()
    print("✓ 所有聊天历史已清空")

    print("\n" + "=" * 60)
    print("✓ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
