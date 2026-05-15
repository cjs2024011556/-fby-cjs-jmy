"""向量化存储模块 - 使用 ChromaDB 存储文档向量"""

from typing import Dict, List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from motoengine.func.embedding import AliyunEmbeddings
from motoengine.func.manual_splitter import ManualSplitter
from motoengine.utils.config import (
    CHAPTERS_DIR,
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIRECTORY,
    MANUAL_FILE,
)


class DocumentEmbedder:
    """文档向量化存储"""

    def __init__(self):
        self.embeddings = AliyunEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        )
        self.vectorstore: Optional[Chroma] = None

    def load_or_create_vectorstore(self, collection_name: str = None) -> Chroma:  # pyright: ignore[reportArgumentType]
        collection_name = collection_name or CHROMA_COLLECTION_NAME

        try:
            self.vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=CHROMA_PERSIST_DIRECTORY,
            )
            try:
                count = self.vectorstore._collection.count()
                if count > 0:
                    print(f"✓ 加载已存在的向量存储，包含 {count} 个文档块")
                else:
                    print("✓ 创建新的向量存储（空）")
            except Exception:
                print("✓ 创建新的向量存储")
        except Exception as e:
            print(f"创建新的向量存储：{e}")
            self.vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=CHROMA_PERSIST_DIRECTORY,
            )

        return self.vectorstore

    def bootstrap_from_sources(self) -> int:
        """如果向量库为空，尝试从维修手册或章节文件自动补齐数据。"""
        try:
            vectorstore = self.load_or_create_vectorstore()
            try:
                if vectorstore._collection.count() > 0:  # pyright: ignore[reportOptionalMemberAccess]
                    return 0
            except Exception:
                pass

            chapters = []
            if MANUAL_FILE.exists():
                try:
                    chapters = ManualSplitter().split_by_chapters()
                except FileNotFoundError:
                    chapters = []
            elif CHAPTERS_DIR.exists():
                chapters = self.load_chapters_from_docs()

            if not chapters:
                return 0

            return self.embed_chapters(chapters)
        except Exception as exc:
            print(f"警告: 自动向量化失败，已跳过：{exc}")
            return 0

    def embed_chapters(self, chapters: List[Dict], batch_size: int = 25) -> int:
        if self.vectorstore is None:
            self.load_or_create_vectorstore()

        all_documents: List[Document] = []

        for chapter in chapters:
            texts = self.text_splitter.split_text(chapter["content"])
            sections_list = [s["id"] for s in chapter.get("sections", [])]
            sections_str = ",".join(sections_list) if sections_list else ""

            for i, text in enumerate(texts):
                doc = Document(
                    page_content=text,
                    metadata={
                        "chapter_id": chapter["chapter_id"],
                        "chapter_number": chapter["chapter_number"],
                        "chapter_name": chapter["chapter_name"],
                        "chunk_index": str(i),
                        "total_chunks": str(len(texts)),
                        "sections": sections_str,
                    },
                )
                all_documents.append(doc)

        total_count = 0
        if all_documents:
            for i in range(0, len(all_documents), batch_size):
                batch = all_documents[i : i + batch_size]
                self.vectorstore.add_documents(batch)  # pyright: ignore[reportOptionalMemberAccess]
                total_count += len(batch)
                print(
                    f"✓ 已处理批次 {i // batch_size + 1}/{(len(all_documents) - 1) // batch_size + 1}，共 {total_count} 个文档块"
                )

            print(f"✓ 成功向量化并存储 {total_count} 个文档块")

        return total_count

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Dict = None,  # pyright: ignore[reportArgumentType]
    ) -> List[Document]:
        if self.vectorstore is None:
            self.load_or_create_vectorstore()

        if filter_dict:
            results = self.vectorstore.similarity_search_with_score(  # pyright: ignore[reportOptionalMemberAccess]
                query, k=k, filter=filter_dict
            )
            return [doc for doc, score in results]
        else:
            return self.vectorstore.similarity_search(query, k=k)  # pyright: ignore[reportOptionalMemberAccess]

    @staticmethod
    def parse_sections(sections_str: str) -> List[str]:
        if not sections_str:
            return []
        return [s.strip() for s in sections_str.split(",") if s.strip()]

    def get_collection_info(self) -> Dict:
        if self.vectorstore is None:
            self.load_or_create_vectorstore()

        try:
            count = self.vectorstore._collection.count()  # pyright: ignore[reportOptionalMemberAccess]
        except Exception:
            count = 0

        chapter_counts = {}
        if count > 0:
            try:
                results = self.vectorstore._collection.get()  # pyright: ignore[reportOptionalMemberAccess]
                for metadata in results.get("metadatas", []):  # pyright: ignore[reportOptionalIterable]
                    chapter_id = metadata.get("chapter_id", "unknown")
                    chapter_counts[chapter_id] = chapter_counts.get(chapter_id, 0) + 1
            except Exception:
                pass

        return {
            "total_chunks": count,
            "chapter_counts": chapter_counts,
            "collection_name": CHROMA_COLLECTION_NAME,
        }

    @staticmethod
    def load_chapters_from_docs():
        if not CHAPTERS_DIR.exists():
            raise FileNotFoundError(f"章节目录不存在：{CHAPTERS_DIR}")

        chapters = []
        for file_path in sorted(CHAPTERS_DIR.glob("第*.md")):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            filename = file_path.stem
            chapters.append(
                {
                    "chapter_id": filename,
                    "chapter_name": filename,
                    "chapter_number": 0,
                    "content": content,
                    "sections": [],
                }
            )

        return chapters
