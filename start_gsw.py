#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GSW學習系統啟動腳本

此腳本用於啟動GSW學習MVP系統，提供完整的系統初始化和測試功能。
系統將自動從.env文件加載配置，並初始化所有組件。

使用方法:
python start_gsw.py
"""

import sys
import os
from pathlib import Path

# 添加項目路徑到sys.path
current_dir = Path(__file__).parent
project_root = current_dir / "gsw-learning-mvp"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def check_environment():
    """檢查運行環境"""
    print("🔍 檢查運行環境...")

    # 檢查Python版本
    import sys
    python_version = sys.version_info
    if python_version < (3, 9):
        print(f"❌ Python版本過低: {python_version.major}.{python_version.minor}")
        print("需要Python 3.9或更高版本")
        return False
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")

    # 檢查.env文件
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ 未找到.env配置文件")
        print("請複製.env.example為.env並填入API密鑰")
        return False
    print("✅ 找到.env配置文件")

    # 檢查必要的依賴
    try:
        import chromadb
        import google.generativeai
        import openai
        import dotenv
        print("✅ 主要依賴包已安裝")
    except ImportError as e:
        print(f"❌ 缺少必要的依賴包: {e}")
        print("請運行: pip install -r gsw-learning-mvp/requirements.txt")
        return False

    return True

def initialize_system():
    """初始化GSW系統"""
    print("\n🚀 初始化GSW學習系統...")

    try:
        from src.gsw_learning_system import GSWLearningSystem

        # 初始化系統
        gsw_system = GSWLearningSystem()
        print("✅ GSW學習系統初始化成功！")

        return gsw_system

    except Exception as e:
        print(f"❌ 系統初始化失敗: {str(e)}")
        print("\n可能的解決方案:")
        print("1. 檢查.env文件中的API密鑰是否正確")
        print("2. 確保網絡連接正常")
        print("3. 檢查防火牆設置")
        print("4. 確認所有依賴包已正確安裝")
        return None

def test_system_functions(system):
    """測試系統基本功能"""
    print("\n🧪 測試系統功能...")

    try:
        # 測試獲取工作空間
        workspace = system.get_current_workspace()
        print("✅ 獲取工作空間成功")

        # 測試處理文本
        test_text = "這是一個測試文本，用於驗證系統功能。"
        print(f"📝 處理測試文本: {test_text}")
        updated_workspace = system.process_text(test_text)
        print("✅ 文本處理成功")

        # 測試查詢功能
        test_query = "測試文本的內容是什麼？"
        print(f"❓ 測試查詢: {test_query}")
        answer = system.query(test_query)
        print(f"✅ 查詢回答: {answer}")

        return True

    except Exception as e:
        print(f"❌ 功能測試失敗: {str(e)}")
        return False

def interactive_mode(system):
    """進入互動模式"""
    print("\n🎮 進入互動模式")
    print("輸入 'help' 查看可用命令，輸入 'quit' 退出")
    print("-" * 50)

    while True:
        try:
            command = input("GSW> ").strip()

            if command.lower() in ['quit', 'exit', 'q']:
                print("👋 再見！")
                break
            elif command.lower() == 'help':
                print_help()
            elif command.startswith('add '):
                # 添加文本
                text = command[4:].strip()
                if text:
                    print(f"📝 添加文本: {text}")
                    result = system.process_text(text)
                    print("✅ 文本已添加到記憶系統")
                else:
                    print("❌ 請提供要添加的文本")
            elif command.startswith('query ') or command.startswith('q '):
                # 查詢
                query = command.split(' ', 1)[1].strip()
                if query:
                    print(f"❓ 查詢: {query}")
                    answer = system.query(query)
                    print(f"🤖 回答: {answer}")
                else:
                    print("❌ 請提供查詢內容")
            elif command.lower() == 'workspace' or command.lower() == 'ws':
                # 顯示工作空間
                workspace = system.get_current_workspace()
                print(f"📚 當前工作空間: {workspace}")
            elif command.lower() == 'clear':
                # 清空控制台
                os.system('cls' if os.name == 'nt' else 'clear')
            else:
                print("❌ 未知命令。輸入 'help' 查看可用命令。")

        except KeyboardInterrupt:
            print("\n👋 用戶中斷，再見！")
            break
        except Exception as e:
            print(f"❌ 命令執行錯誤: {str(e)}")

    return True

def print_help():
    """顯示幫助信息"""
    print("\n📖 可用的命令:")
    print("  add <text>     - 添加文本到記憶系統")
    print("  query <text>   - 向系統提問")
    print("  q <text>       - 查詢的簡寫")
    print("  workspace      - 顯示當前工作空間狀態")
    print("  ws             - workspace的簡寫")
    print("  clear          - 清空控制台")
    print("  help           - 顯示此幫助信息")
    print("  quit           - 退出系統")

def main():
    """主函數"""
    print("=" * 60)
    print("GSW 學習 MVP 系統啟動器")
    print("=" * 60)

    # 環境檢查
    if not check_environment():
        print("\n❌ 環境檢查失敗，請解決上述問題後重試")
        sys.exit(1)

    # 初始化系統
    system = initialize_system()
    if not system:
        print("\n❌ 系統初始化失敗")
        sys.exit(1)

    # 功能測試
    if not test_system_functions(system):
        print("\n⚠️  部分功能測試失敗，但系統仍可繼續運行")
        print("您可以繼續使用，但可能會遇到一些問題")

    # 進入互動模式
    print("\n🎉 系統啟動完成！")
    interactive_mode(system)

if __name__ == "__main__":
    main()