#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GSW系統添加文本和查詢演示腳本

此腳本演示如何先添加文本到GSW學習系統，然後執行查詢。
"""

import sys
import os
from pathlib import Path

# 添加項目路徑到sys.path
current_dir = Path(__file__).parent
project_root = current_dir / "gsw-learning-mvp"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def main():
    """主函數"""
    print("=" * 50)
    print("GSW系統 添加文本和查詢演示")
    print("=" * 50)

    try:
        # 導入GSW學習系統
        from src.gsw_learning_system import GSWLearningSystem

        # 初始化系統
        print("🚀 初始化GSW學習系統...")
        gsw_system = GSWLearningSystem()
        print("✅ 系統初始化成功！")

        # 添加示例文本
        sample_text = "李四於2023年1月15日下午3點在台北市信義區的咖啡廳與王五見面，他們討論了新的AI專案合作計劃。李四提到這個專案預計投資500萬台幣，王五表示很感興趣。"
        print(f"\n📝 添加文本: {sample_text}")
        updated_workspace = gsw_system.process_text(sample_text)
        print("✅ 文本已成功添加到記憶系統")

        # 執行查詢
        query = "李四和王五什麼時候在哪裡見面？他們討論了什麼專案？"
        print(f"\n❓ 執行查詢: {query}")
        answer = gsw_system.query(query)
        print(f"🤖 系統回答: {answer}")

        # 可選：顯示當前工作空間摘要
        workspace = gsw_system.get_current_workspace()
        print("\n📚 當前工作空間包含的實體數量:")
        if 'actors' in workspace:
            print(f"   - 角色/實體: {len(workspace['actors'])} 個")
        print("✅ 演示完成！")

    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {str(e)}")
        print("\n可能的解決方案:")
        print("1. 確保已安裝所有依賴包: pip install -r gsw-learning-mvp/requirements.txt")
        print("2. 檢查.env文件是否存在並包含有效的API密鑰")
        print("3. 確保網路連接正常")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)