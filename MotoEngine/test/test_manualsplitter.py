"""主程序 - 执行文档切分"""

import sys
from pathlib import Path

from motoengine.func import ManualSplitter
from motoengine.utils.config import MANUAL_FILE

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """主函数：切分文档并向量化存储"""
    print("=" * 60)
    print("摩托车发动机维修手册 - 文档切分与向量化")
    print("=" * 60)
    print()

    print("【步骤1】开始切分文档...")
    print(f"文档路径: {MANUAL_FILE}")
    print()

    splitter = ManualSplitter()
    chapters = splitter.split_by_chapters()

    print(f"✓ 成功切分为 {len(chapters)} 个章节")
    print()

    print("章节列表:")
    for chapter in chapters:
        print(
            f"  - 第{chapter['chapter_id']}章: {chapter['chapter_name']} "
            f"({len(chapter['sections'])} 个子章节)"
        )
    print()

    print("【步骤2】保存章节文件...")
    saved_files = splitter.save_chapters(chapters)
    print(f"✓ 已保存 {len(saved_files)} 个章节文件")
    print()


if __name__ == "__main__":
    main()
