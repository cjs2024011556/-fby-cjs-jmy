"""文档切分模块 - 按章节切分维修手册"""

import re
from pathlib import Path
from typing import Dict, List

from motoengine.utils.config import CHAPTERS_DIR, MANUAL_FILE


class ManualSplitter:
    """按章节切分文档"""

    CHAPTER_PATTERN = re.compile(r"^##\s+([一二三四五六七八九十]+)、(.+)$")

    def __init__(self, manual_file: Path = None):  # pyright: ignore[reportArgumentType]
        self.manual_file = manual_file or MANUAL_FILE
        if not self.manual_file.exists():
            raise FileNotFoundError(f"手册文件不存在: {self.manual_file}")

    def split_by_chapters(self) -> List[Dict]:
        with open(self.manual_file, "r", encoding="utf-8") as f:
            content = f.read()

        chapters = []
        lines = content.split("\n")

        current_chapter = None
        current_content = []
        current_sections = []

        for line in lines:
            match = self.CHAPTER_PATTERN.match(line)
            if match:
                if current_chapter is not None:
                    chapters.append(
                        {
                            "chapter_id": current_chapter["id"],
                            "chapter_number": current_chapter["number"],
                            "chapter_name": current_chapter["name"],
                            "content": "\n".join(current_content).strip(),
                            "sections": current_sections.copy(),
                        }
                    )

                chapter_id = match.group(1)
                chapter_name = match.group(2)
                chapter_number = self._chinese_to_number(chapter_id)

                current_chapter = {
                    "id": chapter_id,
                    "number": chapter_number,
                    "name": chapter_name,
                }
                current_content = [line]
                current_sections = []
            else:
                section_match = re.match(r"^###\s+(\d+\.\d+)\s+(.+)$", line)
                if section_match:
                    section_id = section_match.group(1)
                    section_name = section_match.group(2)
                    current_sections.append({"id": section_id, "name": section_name})

                if current_chapter is not None:
                    current_content.append(line)

        if current_chapter is not None:
            chapters.append(
                {
                    "chapter_id": current_chapter["id"],
                    "chapter_number": current_chapter["number"],
                    "chapter_name": current_chapter["name"],
                    "content": "\n".join(current_content).strip(),
                    "sections": current_sections.copy(),
                }
            )

        return chapters

    def _chinese_to_number(self, chinese: str) -> int:
        chinese_numbers = {
            "一": 1,
            "二": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
            "十": 10,
        }
        return chinese_numbers.get(chinese, 0)

    def save_chapters(self, chapters: List[Dict] = None) -> List[Path]:  # pyright: ignore[reportArgumentType]
        if chapters is None:
            chapters = self.split_by_chapters()

        saved_files = []
        for chapter in chapters:
            filename = f"第{chapter['chapter_id']}章_{chapter['chapter_name']}.md"
            filepath = CHAPTERS_DIR / filename

            file_content = f"# {chapter['chapter_name']}\n\n"
            file_content += f"**章节编号**: {chapter['chapter_number']}\n\n"

            if chapter["sections"]:
                file_content += "## 子章节列表\n\n"
                for section in chapter["sections"]:
                    file_content += f"- {section['id']} {section['name']}\n"
                file_content += "\n---\n\n"

            file_content += chapter["content"]

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(file_content)

            saved_files.append(filepath)
            print(f"✓ 已保存章节: {filename}")

        return saved_files

    def get_chapter_metadata(self, chapters: List[Dict] = None) -> List[Dict]:  # pyright: ignore[reportArgumentType]
        if chapters is None:
            chapters = self.split_by_chapters()

        metadata_list = []
        for chapter in chapters:
            metadata = {
                "chapter_id": chapter["chapter_id"],
                "chapter_number": chapter["chapter_number"],
                "chapter_name": chapter["chapter_name"],
                "section_count": len(chapter["sections"]),
                "sections": [s["id"] for s in chapter["sections"]],
            }
            metadata_list.append(metadata)

        return metadata_list
