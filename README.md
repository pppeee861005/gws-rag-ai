# GWS RAG AI - 生成式語義工作空間 RAG 系統

一個全面的 AI 驅動 RAG（檢索增強生成）系統，實現生成式語義工作空間（GSW）框架，具備先進的記憶管理和語義提取能力。

## 🏗️ 專案結構

此倉庫包含多個組件，按以下方式組織：

```
GWS_RAG_AI/
├── gsw-learning-mvp/          # 主要的 GSW 學習 MVP 專案
│   ├── src/                   # 核心源代碼
│   ├── tests/                 # 全面的測試套件
│   ├── data/prompts/          # AI 提示和模板
│   ├── docs/                  # 文檔
│   ├── chroma_db/             # 向量資料庫存儲
│   └── requirements.txt       # Python 依賴
├── list_gpt_models.py         # 獨立的 GPT 模型列表器
├── list_gemini_models.py      # 獨立的 Gemini 模型列表器
├── test_*.py                  # 各種測試和演示腳本
├── add_and_query_demo.py      # 添加/查詢文檔的演示
├── process_file_for_qa.py     # 文件處理工具
├── start_gsw.py              # GSW 系統的主要入口點
└── workspace_manager.py      # 工作空間管理工具
```

## 🚀 主要功能

### 核心 GSW 框架組件
- **操作員 AI 代理**：使用 GPT-4 進行高級實體、角色、狀態和動作分析的語義提取
- **情節記憶系統**：使用 ChromaDB 向量存儲的長期記憶管理
- **調解器**：記憶狀態調解和工作空間更新
- **優化查詢引擎**：具備語義匹配的增強檢索

### AI 整合
- **GPT-4 整合**：最新 OpenAI GPT-4 模型用於語義分析
- **Gemini 支持**：Google Gemini 模型用於替代 AI 處理
- **靈活的 LLM 提供者**：輕鬆在 AI 提供者之間切換
- **向量嵌入**：OpenAI 嵌入用於語義相似性

### 高級能力
- **語義工作空間**：生成式工作空間管理
- **多模態處理**：保留重疊的文本分塊
- **記憶優化**：高效的情節記憶處理
- **提示工程**：針對不同 AI 任務的專業提示

## 🛠️ 安裝和設置

### 先決條件
- Python 3.8+
- OpenAI API 金鑰
- Google Gemini API 金鑰（可選）

### 1. 創建和設置環境
```bash
# 創建虛擬環境
python -m venv gsw-learning-env

# 激活環境 (Windows)
gsw-learning-env\Scripts\activate

# 激活環境 (Linux/Mac)
source gsw-learning-env/bin/activate
```

### 2. 安裝依賴
```bash
cd gsw-learning-mvp
pip install -r requirements.txt
```

### 3. 配置環境變數
```bash
# 複製環境模板
cp .env.example .env

# 使用您的 API 金鑰編輯 .env
# 必需: OPENAI_API_KEY
# 可選: GEMINI_API_KEY
```

## 📋 配置

系統通過 `.env` 文件支持靈活配置：

```env
# AI 提供者設置
LLM_PROVIDER=openai  # 或 'gemini'
OPENAI_MODEL_NAME=gpt-4
GEMINI_MODEL_NAME=gemini-1.5-flash

# API 金鑰
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here

# 向量資料庫
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
CHROMA_PERSIST_DIRECTORY=./chroma_db

# 系統設置
MODEL_TEMPERATURE=0.5
MAX_TOKENS=2048
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
```

## 🎯 使用方法

### 基本使用
```python
from gsw_learning_mvp.src.gsw_learning_system import GSWLearningSystem

# 初始化系統
gsw_system = GSWLearningSystem()

# 處理文本並構建語義工作空間
workspace = gsw_system.process_text("您的文本內容")

# 查詢系統
answer = gsw_system.query("文本中提到了哪些實體？")
```

### 獨立腳本

#### 列出可用的 GPT 模型
```bash
python list_gpt_models.py
```

#### 列出可用的 Gemini 模型
```bash
python list_gemini_models.py
```

#### 啟動 GSW 系統
```bash
python start_gsw.py
```

#### 運行演示
```bash
python add_and_query_demo.py
```

#### 處理文件供問答使用
```bash
# 基本用法 - 使用默認設置處理文件
python process_file_for_qa.py your_file.txt

# 自定義切塊參數
python process_file_for_qa.py document.md --strategy paragraph --chunk-size 800 --overlap 50
```

##### 參數說明
- `file_path`: 要處理的文件路徑（支持 .txt、.md、.json 格式）
- `--strategy`: 切塊策略
  - `fixed`: 固定大小切塊
  - `semantic`: 語義邊界切塊（推薦）
  - `paragraph`: 段落邊界切塊
- `--chunk-size`: 每個chunk的大小（字符數，默認 1000）
- `--overlap`: chunks間重疊大小（字符數，默認 100）

## 🧪 測試

### 運行完整測試套件
```bash
cd gsw-learning-mvp
pytest
```

### 運行特定測試
```bash
# 測試操作員代理
pytest tests/test_operator_ai_agent.py

# 測試語義提取
pytest tests/test_file_reader_properties.py

# 使用覆蓋率測試
pytest --cov=src --cov-report=html
```

### 基於屬性的測試
```bash
# 運行假設屬性測試
pytest tests/test_*_properties.py
```

## 📚 關鍵組件

### 操作員 AI 代理
- **模型**：GPT-4
- **任務**：語義結構提取
- **輸出**：包含實體、角色、狀態、動作、時空上下文的 JSON
- **提示**：`data/prompts/operator_extraction_prompt.md`

### 記憶系統
- **存儲**：帶持久性 SQLite 的 ChromaDB
- **嵌入**：OpenAI text-embedding-ada-002
- **檢索**：語義相似性搜索
- **優化**：情節記憶管理

### 查詢引擎
- **策略**：多階段檢索和生成
- **組件**：實體提取、語義匹配、QA 調解
- **輸出**：上下文相關的答案

## 🔧 開發

### 代碼結構
```
gsw-learning-mvp/src/
├── llms/                    # LLM 適配器 (OpenAI, Gemini)
├── operator_ai_agent.py     # 語義提取代理
├── gsw_learning_system.py   # 主要系統協調器
├── reconciler.py           # 記憶調解
├── optimized_query_engine.py # 查詢處理
├── vector_db_manager.py    # 向量資料庫操作
├── episodic_summary_generator.py # 記憶總結生成器
└── config_manager.py       # 配置管理
```

### 添加新功能
1. 創建功能分支
2. 在 `tests/` 中添加測試
3. 在 `src/` 中實現
4. 更新文檔
5. 運行完整測試套件

### LLM 提供者切換
系統支持動態 LLM 提供者切換：

```python
# 切換到 OpenAI GPT-4
LLM_PROVIDER=openai
OPENAI_MODEL_NAME=gpt-4

# 切換到 Gemini
LLM_PROVIDER=gemini
GEMINI_MODEL_NAME=gemini-1.5-flash
```

## 📖 文檔

- [GSW 框架論文](https://arxiv.org/abs/...) - 原始研究論文
- [API 文檔](gsw-learning-mvp/docs/) - 組件文檔
- [學習總結](gsw-learning-mvp/docs/learning_summary.md) - 實現見解

## 🤝 貢獻

1. Fork 此倉庫
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 許可證

此專案根據 MIT 許可證授權 - 詳見 LICENSE 文件。

## 🙏 致謝

- 基於「超越事實檢索：使用生成式語義工作空間的 RAG 情節記憶」
- OpenAI 提供 GPT-4 API
- Google 提供 Gemini API
- ChromaDB 提供向量存儲
- Python 社群提供優秀的程式庫

## 📞 支持

如有問題和支持：
- 查看現有問題和文檔
- 為錯誤/功能創建新問題
- 查看測試案例以獲取使用示例

---

*用 ❤️ 構建，用於推進 AI 驅動的信息檢索和知識管理*