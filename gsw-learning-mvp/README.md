# GSW 新型 RAG 框架學習 MVP

## 專案概述

本專案是基於論文《Beyond Fact Retrieval: Episodic Memory for RAG with Generative Semantic Workspaces》的學習型 MVP 系統，旨在理解和實踐 GSW 框架的核心概念。

## 專案結構

```
gsw-learning-mvp/
├── src/                    # 源代碼目錄
│   ├── __init__.py
│   ├── file_reader.py      # 文件讀取器
│   └── text_chunker.py     # 文本分塊器
├── tests/                  # 測試目錄
│   ├── __init__.py
│   ├── test_file_reader.py
│   └── test_text_chunker.py
├── data/                   # 數據目錄
├── docs/                   # 文檔目錄
├── requirements.txt        # 依賴包列表
├── .env.example           # 環境配置模板
└── README.md              # 專案說明
```

## 環境設置

### 1. 創建虛擬環境

```bash
# 創建虛擬環境
python -m venv gsw-learning-env

# 激活虛擬環境 (Windows)
gsw-learning-env\Scripts\activate

# 激活虛擬環境 (Linux/Mac)
source gsw-learning-env/bin/activate
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 配置環境變數

```bash
# 複製環境配置模板
copy .env.example .env

# 編輯 .env 文件，填入實際的 API 密鑰
```

## 運行測試

```bash
# 運行所有測試
pytest

# 運行特定測試文件
pytest tests/test_file_reader.py

# 運行屬性測試
pytest tests/test_file_reader_properties.py
```

## 核心組件

### 文件讀取器 (FileReader)
- 支持多種文本格式（.txt、.md、.json 等）
- UTF-8 編碼處理中文內容
- 文件元數據提取

### 文本分塊器 (TextChunker)
- 多種分塊策略（固定大小、語義邊界、段落邊界）
- 保留上下文信息（overlap）
- 塊元數據管理

## 學習目標

1. **GSW 框架理解**
   - Operator AI Agent 的作用和實現
   - Reconciler 組件的記憶狀態遞推與融合機制
   - 情景記憶的概念和應用

2. **技術實現能力**
   - Python 虛擬環境管理
   - 中文開發環境配置
   - 屬性測試的編寫和執行

3. **Kiro 工具掌握**
   - 規格驅動開發流程
   - 任務管理和狀態追蹤
   - 測試和驗證方法

## 注意事項

- 所有開發和測試都在 Python 虛擬環境中進行
- 使用中文進行交流和文檔編寫
- 遵循 AI-First 架構原則
- 確保代碼的正確性和可維護性