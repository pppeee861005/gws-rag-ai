#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GSW 文件處理腳本 - 讀取、切塊、語義提取並保存供QA使用

此腳本將文件內容讀取後進行文本切塊，然後使用GSW學習系統
進行語義提取並保存到向量數據庫中，供後續問答使用。

使用方法:
python process_file_for_qa.py path/to/your/file.txt
python process_file_for_qa.py file.txt --strategy paragraph --chunk-size 800
"""

import argparse
import sys
import logging
import os
from pathlib import Path

# 添加項目路徑到sys.path
project_root = Path(__file__).parent / "gsw-learning-mvp"
os.environ.setdefault("GEMINI_MODEL_NAME", "gemini-2.0-flash")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.file_reader import FileReader
    from src.text_chunker import TextChunker
    from src.gsw_learning_system import GSWLearningSystem
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    print("請確保已安裝依賴包並在正確的目錄中運行")
    sys.exit(1)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_file_for_qa(file_path: str, chunk_strategy: str = "semantic", chunk_size: int = 1000, overlap: int = 100):
    """
    處理單個文件：讀取 -> 切塊 -> 語義提取 -> 保存

    Args:
        file_path: 文件路徑
        chunk_strategy: 切塊策略 ("fixed", "semantic", "paragraph")
        chunk_size: 每個chunk的大小
        overlap: chunk間重疊大小

    Returns:
        bool: 處理是否成功
    """
    print(f"🚀 開始處理文件: {file_path}")

    # 1. 讀取文件
    print("\n📖 階段1: 讀取文件")
    try:
        reader = FileReader()
        result = reader.read_file(file_path)

        if not result['success']:
            print(f"❌ 文件讀取失敗: {result['error_message']}")
            return False

        content = result['content']
        metadata = result['metadata']
        print(f"✓ 文件讀取成功")
        print(f"  - 文件大小: {metadata.file_size} 字節")
        print(f"  - 編碼: {metadata.encoding}")
        print(f"  - 內容長度: {len(content)} 字符")

    except Exception as e:
        print(f"❌ 文件讀取過程發生錯誤: {str(e)}")
        return False

    # 2. 切塊
    print("\n✂️  階段2: 文本切塊")
    try:
        chunker = TextChunker(
            chunk_size=chunk_size,
            overlap=overlap,
            strategy=chunk_strategy
        )
        chunks = chunker.chunk_text(content)

        print(f"✓ 文本切塊完成")
        print(f"  - 切塊策略: {chunk_strategy}")
        print(f"  - chunk大小: {chunk_size} 字符")
        print(f"  - 重疊大小: {overlap} 字符")
        print(f"  - 生成chunks數量: {len(chunks)}")

        if chunks:
            print(f"  - 第一個chunk大小: {chunks[0]['chunk_size']} 字符")
            print(f"  - 最後一個chunk大小: {chunks[-1]['chunk_size']} 字符")

    except Exception as e:
        print(f"❌ 文本切塊過程發生錯誤: {str(e)}")
        return False

    # 3. 初始化GSW系統
    print("\n🧠 階段3: 初始化GSW學習系統")
    try:
        gsw_system = GSWLearningSystem()
        print("✓ GSW學習系統初始化完成")
    except Exception as e:
        print(f"❌ GSW系統初始化失敗: {str(e)}")
        print("請檢查.env配置文件和API密鑰設置")
        return False

    # 4. 處理每個chunk
    print("\n💾 階段4: 語義提取並保存")
    processed_count = 0
    failed_count = 0

    for i, chunk in enumerate(chunks, 1):
        print(f"  處理chunk {i}/{len(chunks)} (大小: {chunk['chunk_size']} 字符)")

        try:
            # 語義提取並保存
            updated_workspace = gsw_system.process_text(chunk['content'])
            processed_count += 1

            # 每處理10個chunks顯示一次進度
            if i % 10 == 0 or i == len(chunks):
                print(f"✓ 已處理 {processed_count}/{len(chunks)} 個chunks")

        except Exception as e:
            print(f"❌ chunk {i} 處理失敗: {str(e)}")
            failed_count += 1
            continue

    # 處理結果統計
    print("\n📊 處理結果統計:")
    print(f"  - 總chunks數: {len(chunks)}")
    print(f"  - 成功處理: {processed_count}")
    print(f"  - 處理失敗: {failed_count}")
    print(f"  - 成功率: {(processed_count/len(chunks)*100):.1f}%")

    if processed_count > 0:
        print("\n🎉 文件處理完成！知識庫已更新，可以開始問答了！")
        return True
    else:
        print("\n❌ 所有chunks處理都失敗了，請檢查配置和API設置")
        return False


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="GSW 文件處理腳本 - 讀取、切塊、語義提取並保存供QA使用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python process_file_for_qa.py document.txt
  python process_file_for_qa.py document.md --strategy paragraph
  python process_file_for_qa.py document.txt --chunk-size 800 --overlap 50

切塊策略:
  fixed     - 固定大小切塊
  semantic  - 語義邊界切塊（推薦）
  paragraph - 段落邊界切塊

支持的文件格式: .txt, .md, .json
        """
    )

    parser.add_argument("file_path", help="要處理的文件路徑")
    parser.add_argument(
        "--strategy",
        choices=["fixed", "semantic", "paragraph"],
        default="semantic",
        help="切塊策略 (默認: semantic)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="每個chunk的大小，字符數 (默認: 1000)"
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=100,
        help="chunks間重疊大小，字符數 (默認: 100)"
    )

    args = parser.parse_args()

    # 檢查文件是否存在
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"❌ 文件不存在: {args.file_path}")
        sys.exit(1)

    # 檢查文件是否為支持的格式
    supported_extensions = {'.txt', '.md', '.json'}
    if file_path.suffix.lower() not in supported_extensions:
        print(f"❌ 不支持的文件格式: {file_path.suffix}")
        print(f"支持的格式: {', '.join(supported_extensions)}")
        sys.exit(1)

    print("=" * 60)
    print("GSW 文件處理腳本")
    print("=" * 60)
    print(f"文件路徑: {args.file_path}")
    print(f"切塊策略: {args.strategy}")
    print(f"chunk大小: {args.chunk_size} 字符")
    print(f"重疊大小: {args.overlap} 字符")
    print("=" * 60)

    # 處理文件
    success = process_file_for_qa(
        str(file_path),
        args.strategy,
        args.chunk_size,
        args.overlap
    )

    print("\n" + "=" * 60)
    if success:
        print("✅ 腳本執行成功！")
        print("\n💡 提示:")
        print("  現在您可以使用以下代碼進行問答:")
        print("  from gsw_learning_mvp.gsw_learning_system import GSWLearningSystem")
        print("  gsw = GSWLearningSystem()")
        print("  answer = gsw.query('您的問題？')")
    else:
        print("❌ 腳本執行失敗！")
        sys.exit(1)


if __name__ == "__main__":
    main()