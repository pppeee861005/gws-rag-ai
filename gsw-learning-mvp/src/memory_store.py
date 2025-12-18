import json
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def load_memory(memory_path: Path) -> Dict[str, Any]:
    """
    從指定路徑的文件中加載 Workspace M_n 的狀態。
    如果文件不存在或內容無效，則返回一個默認的空 Workspace 結構。

    Args:
        memory_path (Path): 記憶文件的路徑。

    Returns:
        Dict[str, Any]: 加載的 Workspace 數據。
    """
    default_workspace = {"actors": [], "events": [], "questions": []} # actors 應該是列表

    if not memory_path.exists():
        logger.info(f"記憶文件 '{memory_path}' 不存在，返回默認空 Workspace 結構。")
        return default_workspace

    try:
        with open(memory_path, 'r', encoding='utf-8') as f:
            workspace = json.load(f)
        
        # 簡單驗證 Workspace 結構並修正可能的舊格式
        if not all(k in workspace for k in ["actors", "events", "questions"]):
            logger.warning(f"記憶文件 '{memory_path}' 內容結構無效或過時，嘗試修正並返回默認結構。")
            return default_workspace

        # 確保 actors, events, questions 至少是列表
        if not isinstance(workspace.get("actors"), list):
            workspace["actors"] = []
        if not isinstance(workspace.get("events"), list):
            workspace["events"] = []
        if not isinstance(workspace.get("questions"), list):
            workspace["questions"] = []

        logger.info(f"成功從 '{memory_path}' 加載 Workspace 數據。")
        return workspace
    except json.JSONDecodeError as e:
        logger.error(f"記憶文件 '{memory_path}' JSON 解碼失敗：{e}，返回默認空 Workspace 結構。", exc_info=True)
        return default_workspace
    except Exception as e:
        logger.error(f"加載記憶文件 '{memory_path}' 時發生未知錯誤：{e}，返回默認空 Workspace 結構。", exc_info=True)
        return default_workspace

def save_memory(workspace: Dict[str, Any], memory_path: Path):
    """
    將 Workspace M_n 的狀態保存到指定路徑的文件中。

    Args:
        workspace (Dict[str, Any]): 要保存的 Workspace 數據。
        memory_path (Path): 記憶文件的路徑。
    """
    # 驗證 Workspace 結構
    if not all(k in workspace for k in ["actors", "events", "questions"]):
        logger.error("要保存的 Workspace 結構無效，缺少必要的鍵 (actors, events, questions)。保存操作中止。")
        raise ValueError("Workspace 結構無效，缺少必要的鍵。")

    # 確保目錄存在
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)
        logger.info(f"成功將 Workspace 數據保存到 '{memory_path}'。")
    except Exception as e:
        logger.error(f"保存記憶文件 '{memory_path}' 時發生錯誤：{e}", exc_info=True)
        raise