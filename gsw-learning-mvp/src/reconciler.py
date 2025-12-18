# reconciler.py
# 記憶狀態遞推與融合模組

from pathlib import Path
import logging
import json
from typing import Dict, Any, List

# 從 src.llms 導入 GeminiLLMAdapter
from .llms.gemini_adapter import GeminiLLMAdapter
# 從 src 導入 memory_store 的 save_memory 和 load_memory
from .memory_store import save_memory
# 導入 SemanticStructure
from .operator_ai_agent import SemanticStructure # Assuming SemanticStructure is defined here

# 配置日誌
logger = logging.getLogger(__name__)

class Reconciler:
    """
    Reconciler 類：負責記憶狀態的遞推與融合學習。
    """
    REQUIRED_WORKSPACE_KEYS = ["actors", "events", "questions"]
    def __init__(self, llm_adapter: GeminiLLMAdapter, qa_reconciliation_prompt_path: Path, memory_file_path: Path):
        self.llm_adapter = llm_adapter
        self.qa_reconciliation_prompt_path = qa_reconciliation_prompt_path
        self.memory_file_path = memory_file_path
        self.workspace = None # Workspace 將在 reconcile 方法中傳入或更新

        if not self.qa_reconciliation_prompt_path.exists():
            logger.error(f"Reconciler 初始化失敗：提示詞文件 '{self.qa_reconciliation_prompt_path}' 不存在。")
            raise FileNotFoundError(f"提示詞文件 '{self.qa_reconciliation_prompt_path}' 不存在。")

        logger.info("Reconciler 初始化完成。 সন")

    def _sanitize_workspace(self, workspace: Any) -> Dict[str, Any]:
        """
        确保 workspace 包含所需键并且每个键都是列表，以便后续保存成功。
        """
        if not isinstance(workspace, dict):
            logger.warning("接收到的 workspace 不是字典，将初始化为空结构。")
            workspace = {}

        sanitized = dict(workspace)
        for key in self.REQUIRED_WORKSPACE_KEYS:
            value = sanitized.get(key)
            if not isinstance(value, list):
                if key not in sanitized:
                    logger.warning(f"workspace 缺少必要键 '{key}'，已插入空列表。")
                else:
                    logger.warning(f"workspace 中 '{key}' 不是列表，已重置为空列表。")
                sanitized[key] = []

        return sanitized

    def load_prompt(self, **kwargs) -> str:
        """
        Load the QA Reconciliation prompt and substitute placeholder blocks
        without triggering format errors when the template contains literal braces.
        """
        with open(self.qa_reconciliation_prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        if not kwargs:
            return template

        prompt = template
        for key, value in kwargs.items():
            placeholder = "{" + key + "}"
            prompt = prompt.replace(placeholder, str(value))
        return prompt

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        封裝 LLM 調用，並處理回應。
        """
        response_dict = self.llm_adapter.generate_content(prompt=prompt)
        return response_dict

    def reconcile(self, prev_workspace: Dict[str, Any], new_semantic_structure: SemanticStructure) -> Dict[str, Any]:
        """
        狀態轉移函數 M_{n-1} → M_n。
        :param prev_workspace: 上一輪記憶狀態 (Workspace)
        :param new_semantic_structure: 新增語義信息 (SemanticStructure 物件)
        :return: 新的記憶狀態 (Workspace)
        """
        logger.info("開始執行記憶狀態遞推與融合。")
        prev_workspace = self._sanitize_workspace(prev_workspace)

        # 將新的語義結構轉換為字典或 JSON 字符串以便傳遞給 LLM
        new_info_json = new_semantic_structure.to_json(ensure_ascii=False)
        prev_workspace_json = json.dumps(prev_workspace, ensure_ascii=False, indent=2)
        current_workspace_json = prev_workspace_json
        unanswered_queries_json = json.dumps(
            prev_workspace.get("questions", []),
            ensure_ascii=False,
            indent=2
        )

        # 整合 QA Reconciliation 提示詞
        prompt = self.load_prompt(
            current_workspace=current_workspace_json,
            new_semantic_structure=new_info_json,
            unanswered_queries=unanswered_queries_json
        )
        
        #調用 Gemini LLM 進行融合
        llm_response = self._call_llm(prompt)
        
        try:
            # 假設 LLM 返回的是一個包含新 workspace 狀態的 JSON 字符串
            updated_workspace_json = llm_response.get("text", "{}")

            # 清理響應內容，移除可能的Markdown代碼塊標記
            updated_workspace_json = updated_workspace_json.strip()
            if updated_workspace_json.startswith("```json"):
                updated_workspace_json = updated_workspace_json[7:]  # 移除 ```json
            elif updated_workspace_json.startswith("```"):
                updated_workspace_json = updated_workspace_json[3:]  # 移除 ```
            if updated_workspace_json.endswith("```"):
                updated_workspace_json = updated_workspace_json[:-3]  # 移除結尾的```
            updated_workspace_json = updated_workspace_json.strip()

            decoder = json.JSONDecoder()
            cleaned = updated_workspace_json.strip()
            first_open = next((idx for idx, ch in enumerate(cleaned) if ch in "{["), None)
            if first_open is None:
                raise json.JSONDecodeError("No JSON object found in LLM response", updated_workspace_json, 0)
            candidate = cleaned[first_open:]
            updated_workspace, _ = decoder.raw_decode(candidate)
        except json.JSONDecodeError as e:
            logger.error(f"LLM 回應解析失敗 (JSON 無效): {e}。回應內容: {llm_response.get('text', '')[:200]}...")
            # 返回原始工作空間或一個空的，取決於錯誤處理策略
            return prev_workspace
        except Exception as e:
            logger.error(f"記憶狀態融合過程中發生未知錯誤: {e}")
            return prev_workspace

        self.workspace = self._sanitize_workspace(updated_workspace)
        logger.info("記憶狀態融合完成。")

        # 持久化新的工作空間狀態
        save_memory(self.workspace, self.memory_file_path)
        logger.info(f"語義工作空間已成功保存至 {self.memory_file_path}。")
        
        return self.workspace

    def align_entities(self, entity_chunks: List[Dict]) -> List[Dict]:
        """
        實體對齊與合併功能（AI-First 架構）
        :param entity_chunks: 來自不同文本片段的實體信息列表
        :return: 對齊並合併後的實體信息
        """
        logger.info("開始執行實體對齊與合併。")
        align_prompt = (
            "你是一個實體對齊專家。請根據下列多個文本片段的實體資訊，識別哪些屬於同一實體，"
            "並對齊其角色、狀態變化、時間和地點，合併為統一的 JSON 結構。\n"
            "請返回合併後的 JSON 結構，並用中文說明合併邏輯。\n"
            f"實體片段: {json.dumps(entity_chunks, ensure_ascii=False, indent=2)}"
        )
        llm_response = self._call_llm(align_prompt)
        try:
            aligned_entities_json = llm_response.get("text", "[]")
            aligned_entities = json.loads(aligned_entities_json)
            # 假設返回的是一個實體列表，並將其合併到當前工作空間的 'actors' 欄位
            if self.workspace and 'actors' in self.workspace:
                # 這裡需要更精細的合併邏輯，目前只是替換或添加到列表中
                # 簡單示範：
                self.workspace['actors'].extend(aligned_entities) 
            logger.info("實體對齊與合併完成。")
            return aligned_entities
        except json.JSONDecodeError as e:
            logger.error(f"實體對齊回應解析失敗 (JSON 無效): {e}。回應內容: {llm_response.get('text', '')[:200]}...")
            return []
        except Exception as e:
            logger.error(f"實體對齊過程中發生未知錯誤: {e}")
            return []

    def update_spatiotemporal_nodes(self, entity_id: str, new_timestamp: str, new_location: str):
        """
        時空節點更新與 Propagate
        :param entity_id: 目標實體 ID
        :param new_timestamp: 新的時間戳記
        :param new_location: 新的地點資訊
        """
        logger.info(f"開始更新實體 {entity_id} 的時空節點。")
        if not self.workspace or 'actors' not in self.workspace:
            logger.warning("工作空間未初始化或缺少 actors 欄位。")
            return

        # 這裡的邏輯需要根據實際的 workspace 結構進行調整，假設 actors 是一個列表，每個 actor 是一個字典
        found_actor = False
        for actor in self.workspace['actors']:
            if actor.get('id') == entity_id: # 假設實體有 'id' 字段
                actor['timestamp'] = new_timestamp
                actor['location'] = new_location
                found_actor = True
                logger.info(f"已為實體 {entity_id} 添加/更新時間戳記與地點。")
                break
        
        if not found_actor:
            logger.warning(f"未在工作空間中找到實體 {entity_id}。")
            return

        # Propagate 給與其互動的其他實體（假設 events 中有互動關係）
        # 此處邏輯需要更精細的實現，例如基於圖數據庫或明確的關聯關係
        logger.warning("時空節點的 Propagate 邏輯尚未完全實現，僅為示意。")
        logger.info("時空節點更新與 propagate 完成。")


    def resolve_conflicts(self) -> Dict[str, Any]:
        """
        邏輯一致性維護與衝突解決（AI-First 架構）
        使用 LLM 確保時間序列因果關係正確、解決實體衝突與重複。
        :return: 修正後的工作空間
        """
        logger.info("開始執行邏輯一致性維護與衝突解決。")
        if not self.workspace:
            logger.warning("工作空間未初始化，無法執行衝突解決。")
            return {}
        
        conflict_prompt = (
            "你是一個邏輯一致性專家。請檢查下列語義工作空間的 actors、events、questions 欄位，確保：\n"
            "1. 時間序列的因果關係正確，無矛盾。\n"
            "2. 空間上下文邏輯一致。\n"
            "3. 識別並解決實體間的衝突與重複。\n"
            "請返回修正後的 JSON 結構，並用中文說明主要調整。\n"
            f"工作空間: {json.dumps(self.workspace, ensure_ascii=False, indent=2)}"
        )
        llm_response = self._call_llm(conflict_prompt)
        try:
            resolved_workspace_json = llm_response.get("text", "{}")
            self.workspace = json.loads(resolved_workspace_json)
            logger.info("邏輯一致性維護與衝突解決完成。")
            return self.workspace
        except json.JSONDecodeError as e:
            logger.error(f"衝突解決回應解析失敗 (JSON 無效): {e}。回應內容: {llm_response.get('text', '')[:200]}...")
            return self.workspace # 返回當前未解決的工作空間
        except Exception as e:
            logger.error(f"衝突解決過程中發生未知錯誤: {e}")
            return self.workspace


    def track_forward_falling_questions(self) -> Dict[str, Any]:
        """
        前瞻性問題追蹤
        - 識別哪些前瞻性問題在新的語義結構中被回答，哪些仍未解決
        - 在 Q 欄位維護完整的問題追蹤信息，記錄回答時間戳和答案內容
        :return: 更新後的工作空間
        """
        logger.info("開始追蹤前瞻性問題的回答狀態。")
        if not self.workspace or 'questions' not in self.workspace:
            logger.warning("工作空間未初始化或缺少 questions 欄位。")
            return self.workspace
        
        track_prompt = (
            "你是一個問題追蹤專家。請根據下列語義工作空間的 questions 欄位，分析每個前瞻性問題：\n"
            "1. 是否已被回答？\n"
            "2. 若已回答，請補全回答內容與回答時間戳。\n"
            "3. 若未解決，請標註狀態為未解決。\n"
            "請返回更新後的 questions JSON 結構，並用中文說明主要變動。\n"
            f"questions: {json.dumps(self.workspace['questions'], ensure_ascii=False, indent=2)}"
        )
        llm_response = self._call_llm(track_prompt)
        try:
            updated_questions_json = llm_response.get("text", "[]")
            self.workspace['questions'] = json.loads(updated_questions_json)
            logger.info("前瞻性問題追蹤完成，Q 欄位已更新。")
            return self.workspace
        except json.JSONDecodeError as e:
            logger.error(f"前瞻性問題追蹤回應解析失敗 (JSON 無效): {e}。回應內容: {llm_response.get('text', '')[:200]}...")
            return self.workspace
        except Exception as e:
            logger.error(f"前瞻性問題追蹤過程中發生未知錯誤: {e}")
            return self.workspace

    def get_workspace(self) -> Dict[str, Any]:
        "獲取當前語義工作空間"
        return self.workspace