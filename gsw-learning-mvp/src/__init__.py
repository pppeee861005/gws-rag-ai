# GSW 學習系統 MVP
# GSW Learning System MVP

"""
GSW 新型 RAG 框架學習 MVP 系統
基於論文《Beyond Fact Retrieval: Episodic Memory for RAG with Generative Semantic Workspaces》
"""

__version__ = "0.1.0"

from .file_reader import FileReader
from .text_chunker import TextChunker
from .config_manager import ConfigurationManager
from .gsw_learning_system import GSWLearningSystem

__all__ = [
    "FileReader",
    "TextChunker",
    "ConfigurationManager",
    "GSWLearningSystem",
]