# GSW 學習 MVP 系統使用指南

## 1. 系統簡介

GSW 學習 MVP 系統是一個基於《Beyond Fact Retrieval: Episodic Memory for RAG with Generative Semantic Workspaces》論文概念的實作，旨在建立一個具有情景記憶和優化查詢能力的 RAG 框架。本系統整合了文本處理、語義提取、記憶融合與持久化、向量檢索以及 LLM 問答等核心功能。

## 2. 環境配置

本系統推薦在 Python 虛擬環境中運行，以確保依賴管理的隔離性。

### 2.1 創建和激活 Python 虛擬環境

1.  **確保安裝 Python 3.9+**:
    ```bash
    python --version
    ```
2.  **在專案根目錄 (D:\gameplace\專案區\GWS研究\GWS_RAG_AI\) 創建虛擬環境**:
    ```bash
    python -m venv venv
    ```
3.  **激活虛擬環境**:
    *   **Windows**:
        ```bash
        ./venv/Scripts/activate
        ```
    *   **macOS / Linux**:
        ```bash
        source venv/bin/activate
        ```

### 2.2 安裝依賴包

激活虛擬環境後，使用 `pip` 安裝 `gsw-learning-mvp/requirements.txt` 中列出的所有依賴包：
```bash
pip install -r gsw-learning-mvp/requirements.txt
```

### 2.3 `.env` 配置說明

本系統使用 `.env` 文件來管理敏感信息（如 API 密鑰）和系統配置。請在 `gsw-learning-mvp/` 目錄下創建一個名為 `.env` 的文件（可以參考 `.env.example`），並填入以下配置項：

```dotenv
# .env 範例配置
# Google Gemini API Key (用於 LLM 互動)
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# OpenAI API Key (用於 Embedding 生成)
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

# OpenAI Embedding 模型名稱
OPENAI_EMBEDDING_MODEL="text-embedding-ada-002"

# 提示詞文件目錄 (相對於 gsw-learning-mvp)
PROMPTS_DIR="gsw-learning-mvp/data/prompts"

# 各組件的提示詞文件名稱
OPERATOR_PROMPT_FILE="operator_pt.md"
RECONCILER_PROMPT_FILE="qa_reconciliation_pt.md"
FINAL_QA_PROMPT_FILE="final_qa_pt.md"

# 記憶文件路徑 (ChromaDB 持久化文件，相對於 gsw-learning-mvp)
MEMORY_FILE_PATH="gsw-learning-mvp/chroma_db/chroma.sqlite3"

# 優化查詢引擎配置
TOP_K_RESULTS=5             # 語義重排序時選擇的 Top-K 摘要數量
SIMILARITY_THRESHOLD=0.7    # 語義相似度篩選閾值
MAX_TOKENS=2048             # LLM 響應的最大 Token 數
MODEL_TEMPERATURE=0.5       # LLM 生成的溫度
```

**請務必替換 `YOUR_GEMINI_API_KEY` 和 `YOUR_OPENAI_API_KEY` 為您自己的有效密鑰。**

## 3. 論文提示詞使用指南

本系統中的 Operator AI Agent、Reconciler 和 Optimized Query Engine 都採用了 AI-First 架構，大量依賴於精心設計的提示詞來指導 LLM 完成語義提取、記憶融合和問答。

提示詞文件位於 `gsw-learning-mvp/data/prompts/` 目錄下，主要包括：

*   **`operator_pt.md` (Operator AI Agent)**: 用於指導 LLM 從輸入文本中提取 `SemanticStructure`（實體、角色、狀態、動作、時空上下文等）。此提示詞預期包含 `{input_text}` 佔位符。
*   **`qa_reconciliation_pt.md` (Reconciler)**: 用於指導 LLM 進行記憶狀態的調和與融合。它接收前一刻的工作空間 `{prev_state_json}` 和新的語義結構 `{new_info_json}`，並輸出更新後的工作空間狀態。
*   **`final_qa_pt.md` (Optimized Query Engine)**: 用於指導 LLM 根據精簡後的上下文回答用戶查詢。它預期包含 `{user_query}`、`{entity_summaries}` 和 `{workspace_context}` 佔位符。

您可以在這些文件中修改提示詞內容，以調整 LLM 的行為和輸出格式。但請確保保留必要的佔位符，以便系統能夠正確注入數據。

## 4. 系統使用說明

`GSWLearningSystem` 是本系統的核心入口點。

### 4.1 初始化系統

```python
from gsw_learning_mvp.gsw_learning_system import GSWLearningSystem

# 系統會自動從 gsw-learning-mvp/.env 加載配置
# 您也可以指定 config_path，例如 GSWLearningSystem(config_path="./my_custom.env")
gsw_system = GSWLearningSystem()
```

### 4.2 處理文本 (更新記憶)

使用 `process_text` 方法將新的文本信息融入到系統的記憶（工作空間）中。這將觸發 Operator AI Agent 進行語義提取，Reconciler 進行記憶融合，並將更新後的記憶持久化。

```python
sample_text = "李四於 2023 年 1 月 15 日下午 3 點在台北市信義區的咖啡廳與王五見面，討論了新的專案合作。他們看起來都很興奮。"
updated_workspace = gsw_system.process_text(sample_text)
print("更新後的工作空間:", updated_workspace)
```

### 4.3 查詢系統 (檢索與問答)

使用 `query` 方法向系統提問。系統將利用優化查詢引擎，從記憶中檢索相關信息，並生成答案。

```python
user_query = "李四和王五在什麼時間地點見面？他們討論了什麼？"
answer = gsw_system.query(user_query)
print("系統回答:", answer)
```

### 4.4 獲取當前工作空間

您可以隨時通過 `get_current_workspace` 方法獲取系統當前的情景記憶狀態。

```python
current_workspace = gsw_system.get_current_workspace()
print("當前工作空間狀態:", current_workspace)
```

## 5. 持久化功能說明

本系統的記憶狀態（工作空間 M_n）是自動持久化的。

*   **記憶文件路徑**: 在 `.env` 文件中通過 `MEMORY_FILE_PATH` 配置。默認為 `gsw-learning-mvp/chroma_db/chroma.sqlite3`。
*   **自動保存**: 每次調用 `process_text` 成功更新工作空間後，`Reconciler` 會自動將最新的工作空間狀態保存到 `MEMORY_FILE_PATH` 指定的文件中。
*   **自動加載**: 系統啟動時，`GSWLearningSystem` 會嘗試從 `MEMORY_FILE_PATH` 加載上次保存的工作空間。如果文件不存在或內容無效，將初始化一個空的默認工作空間。

## 6. 向量數據庫使用指南

本系統使用 `ChromaDB` 作為向量數據庫，並結合 `OpenAI Embedding` 服務來處理文本的語義表示。

*   **配置**:
    *   在 `.env` 中配置 `OPENAI_API_KEY` 和 `OPENAI_EMBEDDING_MODEL`。
    *   `MEMORY_FILE_PATH` 的父目錄 (`gsw-learning-mvp/chroma_db/`) 將作為 `ChromaDB` 的持久化目錄。
*   **功能**:
    *   `VectorDBManager` 負責與 `ChromaDB` 進行交互，包括創建集合、添加文檔、查詢相似文檔以及生成文本的嵌入向量。
    *   `EpisodicSummaryGenerator` 和 `OptimizedQueryEngine` 會內部調用 `VectorDBManager` 來實現語義相似度計算和摘要嵌入等功能。

通常情況下，您無需直接與 `VectorDBManager` 交互，它作為系統的後端組件自動運行。系統會利用向量數據庫來實現語義重排序，以確保查詢結果的相關性和質量。