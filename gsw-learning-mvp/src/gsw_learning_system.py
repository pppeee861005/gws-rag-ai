# gsw-learning-mvp/src/gsw_learning_system.py

import os
from .config_manager import ConfigurationManager
from .llms.base import BaseLlm
from .llms.gemini import Gemini
from .llms.openai import OpenAI
from .llms.gemini_adapter import GeminiLLMAdapter
from .operator_ai_agent import OperatorAIAgent
from .reconciler import Reconciler
from .optimized_query_engine import OptimizedQueryEngine
from .memory_store import load_memory, save_memory
from .vector_db_manager import VectorDBManager
from .episodic_summary_generator import EpisodicSummaryGenerator
import logging
from pathlib import Path

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GeminiAdapter:
    """
    Lightweight wrapper to unify the interface expected by the rest of the pipeline.
    """

    def __init__(self, llm_instance: BaseLlm):
        if not llm_instance:
            raise ValueError("LLM instance must be provided to GeminiAdapter.")
        self.llm = llm_instance

    def generate_content(self, prompt: str, **kwargs) -> dict:
        if not prompt:
            raise ValueError("prompt must be provided")
        return self.llm.generate_content(prompt, **kwargs)

class GSWLearningSystem:
    def __init__(self, config_path: str = None):
        """
        初始化 GSWLearningSystem。
        整合配置管理器、Gemini 適配器、Operator AI Agent、Reconciler 和優化查詢引擎。
        """
        logger.info("正在初始化 GSWLearningSystem...")

        # 1. 初始化配置管理器
        actual_config_path = Path(config_path) if config_path else Path("gsw-learning-mvp/.env")
        self.config_manager = ConfigurationManager(actual_config_path)
        logger.info("配置管理器初始化完成。")

        # 2. Initialize the LLM adapter
        provider = self.config_manager.llm_provider
        if provider == "openai":
            openai_model = self.config_manager.get('OPENAI_MODEL_NAME', 'gpt-4')
            openai_api_key = self.config_manager.get('OPENAI_API_KEY')
            if not openai_api_key:
                logger.error("OPENAI_API_KEY is missing, please configure .env")
                raise ValueError("OPENAI_API_KEY must be set")
            real_llm = OpenAI(model=openai_model, api_key=openai_api_key)
            self.llm_adapter = real_llm  # OpenAI instance directly
            logger.info(f"OpenAI GPT adapter initialized with {openai_model}")
        else:
            gemini_api_key = self.config_manager.get('GEMINI_API_KEY')
            if not gemini_api_key:
                logger.error("GEMINI_API_KEY is missing, please configure .env")
                raise ValueError("GEMINI_API_KEY must be set")
            gemini_model = self.config_manager.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash')
            real_llm = Gemini(model=gemini_model)
            self.llm_adapter = GeminiLLMAdapter(gemini=real_llm)
            logger.info(f"Gemini LLM adapter initialized with {gemini_model}")
        # 3. 初始化持久化管理器 (load_memory)
        # memory_file_path 現在指向 ChromaDB 的文件，其父目錄將作為 ChromaDB 的持久化目錄
        self.memory_file_path = Path(self.config_manager.get('MEMORY_FILE_PATH', 'gsw-learning-mvp/chroma_db/chroma.sqlite3'))
        self.workspace = load_memory(self.memory_file_path)
        logger.info(f"工作空間從 '{self.memory_file_path}' 加載完成。")

        # 4. 初始化 VectorDBManager
        openai_api_key = self.config_manager.get('OPENAI_API_KEY')
        embedding_model = self.config_manager.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')
        if not openai_api_key:
            logger.error("OPENAI_API_KEY 未配置。向量數據庫管理器初始化失敗。")
            raise ValueError("OPENAI_API_KEY 未配置。")
        self.vector_db_manager = VectorDBManager(
            persist_directory=str(self.memory_file_path.parent), # 使用 chroma.sqlite3 的父目錄作為持久化目錄
            openai_api_key=openai_api_key,
            embedding_model=embedding_model
        )
        logger.info("VectorDBManager 初始化完成。")

        # 5. 初始化 EpisodicSummaryGenerator
        self.episodic_summary_generator = EpisodicSummaryGenerator(
            llm_adapter=self.llm_adapter,
            vector_db_manager=self.vector_db_manager,
            config_manager=self.config_manager
        )
        logger.info("EpisodicSummaryGenerator 初始化完成。")

        # 6. 初始化 Operator AI Agent
        prompts_dir = Path(self.config_manager.get('PROMPTS_DIR', 'gsw-learning-mvp/data/prompts'))
        operator_prompt_filename = self.config_manager.get('OPERATOR_PROMPT_FILE', 'operator_pt.md')
        operator_prompt_path = prompts_dir / operator_prompt_filename
        self.operator_agent = OperatorAIAgent(
            llm_adapter=self.llm_adapter,
            prompt_path=operator_prompt_path
        )
        logger.info("Operator AI Agent 初始化完成。")

        # 7. 初始化 Reconciler
        reconciler_prompt_filename = self.config_manager.get('RECONCILER_PROMPT_FILE', 'qa_reconciliation_pt.md')
        reconciler_prompt_path = prompts_dir / reconciler_prompt_filename
        self.reconciler = Reconciler(
            llm_adapter=self.llm_adapter,
            qa_reconciliation_prompt_path=reconciler_prompt_path,
            memory_file_path=self.memory_file_path
        )
        logger.info("Reconciler 初始化完成。")

        # 8. 初始化優化查詢引擎
        final_qa_prompt_filename = self.config_manager.get('FINAL_QA_PROMPT_FILE', 'final_qa_pt.md')
        final_qa_prompt_path = prompts_dir / final_qa_prompt_filename
        self.optimized_query_engine = OptimizedQueryEngine(
            llm_adapter=self.llm_adapter,
            vector_db_manager=self.vector_db_manager,
            episodic_summary_generator=self.episodic_summary_generator,
            operator_agent=self.operator_agent,
            config_manager=self.config_manager,
            memory_file_path=self.memory_file_path,
            final_qa_prompt_path=final_qa_prompt_path
        )
        logger.info("優化查詢引擎初始化完成。")

        logger.info("GSWLearningSystem 初始化成功。")

    def process_text(self, text: str) -> dict:
        """
        實現完整的 GSW 處理流程：
        1. Operator AI Agent 提取語義結構。
        2. Reconciler 處理語義結構，更新工作空間。
        3. 持久化工作空間 (由 Reconciler 處理)。
        """
        logger.info("開始處理文本。")

        # 1. Operator AI Agent 提取語義結構
        semantic_structure = self.operator_agent.extract_semantic_structure(text)
        logger.info("Operator AI Agent 已提取語義結構。")

        # 2. Reconciler 處理語義結構，更新工作空間
        updated_workspace = self.reconciler.reconcile(self.workspace, semantic_structure)
        self.workspace = updated_workspace
        logger.info("Reconciler 已更新工作空間。")

        # 持久化由 Reconciler 內部處理
        logger.info("工作空間已持久化 (由 Reconciler 處理)。")

        return self.workspace

    def query(self, user_query: str) -> str:
        """
        使用優化查詢引擎處理用戶查詢。
        """
        logger.info(f"開始處理查詢: {user_query}")
        answer = self.optimized_query_engine.query(user_query, self.workspace)
        logger.info("查詢處理完成。")
        return answer

    def get_current_workspace(self) -> dict:
        """
        獲取當前的工作空間。
        """
        return self.workspace