"""测试文档向量化模块"""

from motoengine.func.document_vector import DocumentEmbedder
from motoengine.utils.config import CHAPTERS_DIR, CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIRECTORY


def main():
    """主函数：加载已切割文档并向量化"""
    print("=" * 60)
    print("文档向量化 - 读取已切割文档")
    print("=" * 60)

    print("\n向量数据库配置:")
    print(f"  - 存储位置：{CHROMA_PERSIST_DIRECTORY}")
    print(f"  - 集合名称：{CHROMA_COLLECTION_NAME}")

    embedder = DocumentEmbedder()

    print(f"\n从 {CHAPTERS_DIR} 加载文档...")
    chapters = DocumentEmbedder.load_chapters_from_docs()
    print(f"✓ 已加载 {len(chapters)} 个章节")

    print("\n开始向量化存储...")
    embedder.load_or_create_vectorstore()

    total_chunks = embedder.embed_chapters(chapters)
    print(f"✓ 共存储 {total_chunks} 个文档块")

    print("\n向量存储统计:")
    info = embedder.get_collection_info()
    print(f"  - 集合名称：{info['collection_name']}")
    print(f"  - 总文档块数：{info['total_chunks']}")

    print("\n" + "=" * 60)
    print("测试查询功能")
    print("=" * 60)

    query = "火花塞的型号是什么？"
    print(f"\n查询：{query}")
    results = embedder.search(query, k=3)
    print(f"  找到 {len(results)} 个相关结果:")
    for i, doc in enumerate(results, 1):
        chapter = doc.metadata.get("chapter_name", "未知")
        content_preview = doc.page_content[:100].replace("\n", " ")
        print(f"    {i}. [{chapter}] {content_preview}...")

    print("\n" + "=" * 60)
    print("✓ 完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
