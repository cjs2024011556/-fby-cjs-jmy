#!/usr/bin/env python3
"""
嵌入模型测试文件
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_embedding_model():
    """测试嵌入模型功能"""
    try:
        from motoengine.func.embedding import embedding_model

        test_text = "小孩发烧怎么办"

        print(f"测试文本：{test_text}")
        vector = embedding_model.embed_query(test_text)

        print(f"向量维度：{len(vector)}")
        print(f"向量前 10 位：{vector[:10]}")

        print("\n✅ 嵌入模型测试成功!")
        return True

    except Exception as e:
        print(f"\n❌ 嵌入模型测试失败：{e}")
        print("请确保已正确配置阿里云百炼 API 密钥 (DASHSCOPE_API_KEY) 和相关参数")
        return False


def test_embed_documents():
    """测试批量文档嵌入功能"""
    try:
        from motoengine.func.embedding import embedding_model

        test_texts = [
            "摩托车发动机无法启动怎么办",
            "如何更换火花塞",
            "发动机异响的原因有哪些",
        ]

        print(f"测试批量嵌入，文档数量：{len(test_texts)}")
        vectors = embedding_model.embed_documents(test_texts)

        print(f"返回向量数量：{len(vectors)}")
        print(f"每个向量维度：{len(vectors[0])}")
        print(f"第一个向量前 10 位：{vectors[0][:10]}")

        print("\n✅ 批量嵌入测试成功!")
        return True

    except Exception as e:
        print(f"\n❌ 批量嵌入测试失败：{e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("嵌入模型测试")
    print("=" * 50)

    success1 = test_embedding_model()

    print()

    success2 = test_embed_documents()

    print()
    if success1 and success2:
        print(" 所有测试通过!")
    else:
        print("⚠️ 部分测试失败")
