# Operator AI Agent
# Implementation of the basic Operator AI Agent class for semantic extraction learning

from pathlib import Path
import json
import logging
from typing import Dict, Any, List
import inspect

from .text_chunker import TextChunker
from .llms.openai import OpenAI  # Import OpenAI LLM

# Configure logging
logger = logging.getLogger(__name__)

class SemanticStructure:
    """
    Semantic structure data model according to paper specifications
    """
    def __init__(
        self,
        entities: List[Dict] = None,
        events: List[Dict] = None,
        questions: List[Dict] = None,
        roles: List[Dict] = None,
        states: List[Dict] = None,
        actions: List[Dict] = None,
        spatiotemporal_context: List[Dict] = None,
        forward_falling_questions: List[Dict] = None,
    ):
        self.entities = entities or []
        self.events = events or []
        self.questions = questions or []
        self.roles = roles or []
        self.states = states or []
        self.actions = actions or []
        self.spatiotemporal_context = spatiotemporal_context or []
        self.forward_falling_questions = forward_falling_questions or []

    def to_dict(self):
        return {
            "entities": self.entities,
            "events": self.events,
            "questions": self.questions,
            "roles": self.roles,
            "states": self.states,
            "actions": self.actions,
            "spatiotemporal_context": self.spatiotemporal_context,
            "forward_falling_questions": self.forward_falling_questions
        }

    def to_json(self, ensure_ascii=False, indent=2):
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=indent)

class OperatorAIAgent:
    """
    Operator AI Agent for semantic extraction learning, integrating OpenAI GPT LLM and prompts.
    """
    def __init__(self, llm_adapter: OpenAI, prompt_path: Path):
        self.llm_adapter = llm_adapter
        self.prompt_path = prompt_path

        if not self.prompt_path.exists():
            logger.error(f"Operator AI Agent initialization failed: prompt file '{self.prompt_path}' does not exist.")
            raise FileNotFoundError(f"Prompt file '{self.prompt_path}' does not exist.")

        logger.info(f"Operator AI Agent initialized with prompt: {self.prompt_path.name}")

    def load_prompt(self, **kwargs) -> str:
        """
        Load operator prompt with optional parameter formatting.
        """
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        logger.debug(f"load_prompt called with kwargs keys: {list(kwargs.keys())}, values: {list(kwargs.values())[:3] if kwargs else 'empty'}")
        
        # 使用 replace 代替 format，避免 JSON 中的大括號被誤認為是變數
        result = template
        if kwargs:
            for key, value in kwargs.items():
                placeholder = "{" + key + "}"
                result = result.replace(placeholder, str(value))
        
        return result

    def run(self, text: str, **kwargs) -> str:
        """
        執行語義提取主流程。
        text: 輸入文本
        kwargs: 可選參數傳遞給 prompt
        return: LLM 回應內容 (純文本)
        """
        prompt = self.load_prompt(input_text=text, **kwargs) # 將文本作為 input_text 傳遞給 prompt
        response_dict = self.llm_adapter.generate_content(prompt=prompt)
        # 預設回傳 LLM 內容的 "text" 部分
        return response_dict.get("text", "")

    def extract_semantic_structure(self, text: str, chunk_strategy: str = "fixed", 
                                   chunk_size: int = 1000, overlap: int = 100, **kwargs) -> SemanticStructure:
        """
        語義結構提取主流程：
        1. 文本分塊
        2. 逐 chunk 調用 LLM 提取語義結構
        3. 合併所有 chunk 結果
        4. 返回 SemanticStructure 物件
        """
        logger.info(f"開始提取語義結構，文本長度：{len(text)}")
        chunker = TextChunker(chunk_size=chunk_size, overlap=overlap, strategy=chunk_strategy)
        chunks = chunker.chunk_text(text)
        
        logger.debug("LLM adapter type: %s (%s)", type(self.llm_adapter), getattr(self.llm_adapter, "__module__", None))
        try:
            signature = inspect.signature(self.llm_adapter.generate_content)
        except (ValueError, TypeError):
            signature = None
        logger.debug("generate_content signature: %s", signature)

        all_entities, all_roles, all_states, all_actions, all_ctx, all_questions = [], [], [], [], [], []

        for i, chunk in enumerate(chunks):
            chunk_text = chunk["content"]
            logger.debug(f"正在處理第 {i+1}/{len(chunks)} 個 chunk (長度: {len(chunk_text)})")
            
            # 準備傳遞給 prompt 的參數，確保 input_text 包含在內
            prompt_kwargs = {"input_text": chunk_text}
            prompt_kwargs.update(kwargs)

            try:
                # 假設 operator_pt.md 包含 '{input_text}' 佔位符
                prompt = self.load_prompt(**prompt_kwargs)
                llm_response_dict = self.llm_adapter.generate_content(prompt=prompt)
                
                # 確保 LLM 返回的內容是有效的 JSON 字符串
                response_content = llm_response_dict.get("text", "{}")

                # 增強的 JSON 清理邏輯
                response_content = response_content.strip()
                
                # 1. 嘗試提取 Markdown 代碼塊中的內容
                if "```json" in response_content:
                    start_idx = response_content.find("```json") + 7
                    end_idx = response_content.find("```", start_idx)
                    if end_idx != -1:
                        response_content = response_content[start_idx:end_idx]
                    else:
                        response_content = response_content[start_idx:]
                elif "```" in response_content:
                     # 處理沒有指定 json 語言的代碼塊，或者結尾
                    start_idx = response_content.find("```") + 3
                    end_idx = response_content.find("```", start_idx)
                    if end_idx != -1:
                        response_content = response_content[start_idx:end_idx]
                    else:
                        response_content = response_content[start_idx:]
                
                response_content = response_content.strip()

                # 2. 如果還是無法解析，嘗試尋找最外層的 {}
                if not response_content.startswith("{"):
                    start_idx = response_content.find("{")
                    if start_idx != -1:
                        response_content = response_content[start_idx:]
                
                if not response_content.endswith("}"):
                    end_idx = response_content.rfind("}")
                    if end_idx != -1:
                        response_content = response_content[:end_idx+1]

                # 3. 嘗試解析
                try:
                    result = json.loads(response_content)
                except json.JSONDecodeError:
                    # 如果標準解析失敗，嘗試使用 regex 修復常見錯誤 (例如 trailing commas)
                    import re
                    # 移除物件最後一個屬性後的逗號
                    response_content = re.sub(r',(\s*})', r'\1', response_content)
                    # 移除陣列最後一個元素後的逗號
                    response_content = re.sub(r',(\s*])', r'\1', response_content)
                    result = json.loads(response_content)

                all_entities.extend(result.get("entities", []))
                all_roles.extend(result.get("roles", []))
                all_states.extend(result.get("states", []))
                all_actions.extend(result.get("actions", []))
                all_ctx.extend(result.get("spatiotemporal_context", []))
                all_questions.extend(result.get("forward_falling_questions", [])) # 從每個 chunk 提取前瞻性問題

            except json.JSONDecodeError as e:
                logger.error(f"chunk {i+1} 的語義結構解析失敗 (JSON 無效): {e}。回應內容: {response_content[:200]}...")
            except Exception as e:
                logger.error(f"chunk {i+1} 的語義結構提取過程中發生未知錯誤: {e}")
        
        semantic_structure = SemanticStructure(
            entities=all_entities,
            roles=all_roles,
            states=all_states,
            actions=all_actions,
            spatiotemporal_context=all_ctx,
            forward_falling_questions=all_questions # 將收集到的前瞻性問題傳入
        )
        logger.info("語義結構提取完成。 সন")
        return semantic_structure

    def extract_forward_falling_questions(self, semantic_structure: SemanticStructure, **kwargs) -> SemanticStructure:
        """
        從語義結構推導前瞻性問題，並回傳擴充後的 SemanticStructure。
        採用 AI-First 架構，將 roles、states、actions、時空資訊組合，交由 LLM 產生前瞻性問題。
        """
        logger.info("開始提取前瞻性問題。 সন")
        
        # 準備 LLM 輸入
        context = {
            "roles": semantic_structure.roles,
            "states": semantic_structure.states,
            "actions": semantic_structure.actions,
            "spatiotemporal_context": semantic_structure.spatiotemporal_context
        }
        
        # 這裡可以載入一個專門用於提取前瞻性問題的提示詞，或者直接構建
        # 假設 operator_pt.md 也可以包含一個用於生成前瞻性問題的模板
        prompt_template_for_questions = (
            "你是一個語義推理專家，請根據下列語義結構資訊，推導出所有合理的前瞻性問題（例如：被逮捕後會在什麼時候被起訴、審判會在哪裡、會不會交保等）。\n"
            "請以 JSON 陣列格式輸出所有前瞻性問題，每個問題需包含：question (string), related_entities (list of strings), reasoning_context (string)。\n"
            f"語義結構：{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
        
        try:
            llm_response_dict = self.llm_adapter.generate_content(prompt=prompt_template_for_questions)
            questions_json_str = llm_response_dict.get("text", "[]")

            # 清理響應內容，移除可能的Markdown代碼塊標記
            questions_json_str = questions_json_str.strip()
            if questions_json_str.startswith("```json"):
                questions_json_str = questions_json_str[7:]  # 移除 ```json
            if questions_json_str.startswith("```"):
                questions_json_str = questions_json_str[3:]  # 移除 ```
            if questions_json_str.endswith("```"):
                questions_json_str = questions_json_str[:-3]  # 移除結尾的```
            questions_json_str = questions_json_str.strip()

            questions = json.loads(questions_json_str)
            
            # 確保 questions 是一個列表
            if not isinstance(questions, list):
                logger.warning(f"LLM 返回的前瞻性問題不是列表格式，嘗試修正。回應: {questions_json_str}")
                questions = []

        except json.JSONDecodeError as e:
            logger.error(f"前瞻性問題解析失敗 (JSON 無效): {e}。回應內容: {questions_json_str[:200]}...")
            questions = []
        except Exception as e:
            logger.error(f"提取前瞻性問題過程中發生未知錯誤: {e}")
            questions = []
        
        # 將新提取的前瞻性問題添加到 SemanticStructure 的 forward_falling_questions 列表中
        semantic_structure.forward_falling_questions.extend(questions)
        logger.info(f"前瞻性問題提取完成，新增 {len(questions)} 個問題。 সন")
        return semantic_structure