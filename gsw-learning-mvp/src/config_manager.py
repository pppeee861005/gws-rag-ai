import os
from dotenv import load_dotenv, dotenv_values
from pathlib import Path
from typing import Any, Dict, Optional

class ConfigurationManager:
    """
    配置管理器，用於加載和驗證 .env 文件中的環境變數。
    """
    def __init__(self, env_path: Path, override: bool = False):
        """
        初始化配置管理器。

        Args:
            env_path (Path): .env 文件的絕對路徑。
            override (bool): 是否用 .env 文件中的值覆蓋已存在的環境變數。
        """
        self.env_path = env_path
        
        if not os.path.exists(self.env_path):
            raise FileNotFoundError(f"錯誤：找不到環境配置文件 '{self.env_path}'。請確保文件存在或路徑正確。")

        # 使用 dotenv_values 加載，避免直接覆蓋系統環境變數，並確保只加載一次
        env_values = dotenv_values(dotenv_path=self.env_path)
        for key, value in env_values.items():
            if override or os.getenv(key) is None:
                os.environ[key] = value

        self._load_and_validate_config()

    def _load_and_validate_config(self):
        """
        加載和驗證所有配置項。
        """
        self._load_llm_config()
        self._load_system_config()
        # 其他配置加載可以在此處添加

    def _load_llm_config(self):
        """
        Load the configuration needed to choose the active LLM provider.
        """
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.llm_provider = provider

        self.llm_configs = {
            "gemini": {
                "api_key": os.getenv("GEMINI_API_KEY"),
                "model_name": os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model_name": os.getenv("OPENAI_MODEL_NAME", "gpt-4"),
                "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"),
            }
        }

        provider_config = self.llm_configs.get(provider)
        if not provider_config or not provider_config.get("api_key"):
            raise ValueError(f"Missing API key for the configured LLM provider '{provider}'.")

        try:
            self.model_temperature = float(os.getenv("MODEL_TEMPERATURE", 0.5))
            self.max_tokens = int(os.getenv("MAX_TOKENS", 2048))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Model temperature or max tokens must be numeric: {e}")

    def get_llm_config(self, provider: str) -> dict:
        """
        獲取指定 LLM 提供者的配置。

        Args:
            provider (str): LLM 提供者名稱 (e.g., "gemini", "openai").

        Returns:
            一個包含該提供者配置的字典。
        """
        config = self.llm_configs.get(provider.lower())
        if not config:
            raise ValueError(f"錯誤：找不到名為 '{provider}' 的 LLM 提供者配置。")
        return config



    def _load_system_config(self):
        """
        加載和驗證系統運行相關的配置。
        """
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"錯誤：無效的日誌級別 '{self.log_level}'。可選值為：{', '.join(valid_log_levels)}")

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        獲取指定鍵的配置值。

        Args:
            key (str): 配置項的鍵。
            default (Any, optional): 如果鍵不存在時返回的默認值。

        Returns:
            Any: 配置值或默認值。
        """
        return os.getenv(key, default)