# -*- coding: utf-8 -*-
"""
文本分塊器模組 (Text Chunker Module)

將長文本分割成適當大小的 chunks，支持多種分塊策略，
保留上下文信息，為後續語義提取做準備。

需求：1.1, 1.2, 1.3, 1.4
"""

import uuid
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

# 配置中文日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("文本分塊器")


class ChunkingStrategy(Enum):
    """分塊策略枚舉"""
    FIXED = "fixed"           # 固定大小分塊
    SEMANTIC = "semantic"     # 語義邊界分塊
    PARAGRAPH = "paragraph"   # 段落邊界分塊


@dataclass
class ChunkMetadata:
    """Chunk 元數據"""
    chunk_id: str
    source_text_position: int  # chunk 在原始文本中的起始位置
    chunk_size: int            # chunk 的大小（字符數）
    overlap_before: Optional[str] = None  # 前一個 chunk 的 ID
    overlap_after: Optional[str] = None   # 後一個 chunk 的 ID
    overlap_size: int = 0      # 重疊大小


@dataclass
class Chunk:
    """文本塊數據結構"""
    content: str
    metadata: ChunkMetadata
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            "chunk_id": self.metadata.chunk_id,
            "content": self.content,
            "source_text_position": self.metadata.source_text_position,
            "chunk_size": self.metadata.chunk_size,
            "overlap_info": {
                "before": self.metadata.overlap_before,
                "after": self.metadata.overlap_after,
                "size": self.metadata.overlap_size
            }
        }


class TextChunker:
    """
    文本分塊器 - 將長文本分割成適當大小的 chunks
    
    支持多種分塊策略：
    - fixed: 固定大小分塊
    - semantic: 語義邊界分塊（基於句子邊界）
    - paragraph: 段落邊界分塊
    
    需求：1.1, 1.2, 1.3, 1.4
    """
    
    def __init__(
        self, 
        chunk_size: int = 1000, 
        overlap: int = 100, 
        strategy: str = "fixed"
    ):
        """
        初始化文本分塊器
        
        Args:
            chunk_size: 每個 chunk 的目標大小（字符數）
            overlap: chunks 之間的重疊大小（字符數），用於保留上下文
            strategy: 分塊策略，支持 "fixed"、"semantic"、"paragraph"
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._validate_and_set_strategy(strategy)
        
        self.log_chunking_info(
            f"初始化文本分塊器 - 策略: {self.strategy.value}, "
            f"塊大小: {chunk_size}, 重疊: {overlap}"
        )
    
    def _validate_and_set_strategy(self, strategy: str) -> None:
        """驗證並設置分塊策略"""
        try:
            self.strategy = ChunkingStrategy(strategy)
        except ValueError:
            valid_strategies = [s.value for s in ChunkingStrategy]
            raise ValueError(
                f"無效的分塊策略: {strategy}。"
                f"有效策略: {valid_strategies}"
            )
    
    def set_chunking_strategy(self, strategy: str) -> None:
        """設置分塊策略"""
        self._validate_and_set_strategy(strategy)
        self.log_chunking_info(f"分塊策略已更改為: {self.strategy.value}")
    
    def chunk_text(self, text: str) -> List[Dict]:
        """
        將文本分塊
        
        Args:
            text: 要分塊的原始文本
        
        Returns:
            List[Dict]: 包含以下信息的 chunks 列表：
                - chunk_id: 唯一的 chunk 標識符
                - content: chunk 的文本內容
                - source_text_position: chunk 在原始文本中的起始位置
                - chunk_size: chunk 的大小（字符數）
                - overlap_info: 重疊信息（前後 chunks 的 ID）
        """
        if not text or not text.strip():
            self.log_chunking_info("輸入文本為空，返回空列表")
            return []
        
        self.log_chunking_info(f"開始分塊處理，文本長度: {len(text)} 字符")
        
        # 根據策略選擇分塊方法
        if self.strategy == ChunkingStrategy.FIXED:
            chunks = self._chunk_fixed(text)
        elif self.strategy == ChunkingStrategy.SEMANTIC:
            chunks = self._chunk_semantic(text)
        elif self.strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_paragraph(text)
        else:
            chunks = self._chunk_fixed(text)
        
        # 設置重疊信息
        self._set_overlap_info(chunks)
        
        self.log_chunking_info(f"分塊完成，共生成 {len(chunks)} 個 chunks")
        
        return [chunk.to_dict() for chunk in chunks]
    
    def _chunk_fixed(self, text: str) -> List[Chunk]:
        """固定大小分塊"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # 計算結束位置
            end = min(start + self.chunk_size, text_length)
            
            # 提取 chunk 內容
            content = text[start:end]
            
            # 創建元數據
            metadata = ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                source_text_position=start,
                chunk_size=len(content),
                overlap_size=self.overlap if start > 0 else 0
            )
            
            chunks.append(Chunk(content=content, metadata=metadata))
            
            # 計算下一個起始位置（考慮重疊）
            start = end - self.overlap if end < text_length else text_length
            
            # 防止無限循環
            if start >= text_length:
                break
        
        return chunks
    
    def _chunk_semantic(self, text: str) -> List[Chunk]:
        """語義邊界分塊（基於句子邊界）"""
        # 使用正則表達式分割句子（支持中英文標點）
        sentence_pattern = r'(?<=[。！？.!?])\s*'
        sentences = re.split(sentence_pattern, text)
        sentences = [s for s in sentences if s.strip()]
        
        if not sentences:
            return self._chunk_fixed(text)
        
        chunks = []
        current_content = ""
        current_start = 0
        position = 0
        
        for sentence in sentences:
            # 如果添加這個句子會超過 chunk_size
            if len(current_content) + len(sentence) > self.chunk_size and current_content:
                # 保存當前 chunk
                metadata = ChunkMetadata(
                    chunk_id=str(uuid.uuid4()),
                    source_text_position=current_start,
                    chunk_size=len(current_content),
                    overlap_size=self.overlap if chunks else 0
                )
                chunks.append(Chunk(content=current_content, metadata=metadata))
                
                # 計算重疊部分
                overlap_content = current_content[-self.overlap:] if self.overlap > 0 else ""
                current_start = position - len(overlap_content)
                current_content = overlap_content + sentence
            else:
                current_content += sentence
            
            position += len(sentence)
        
        # 處理最後一個 chunk
        if current_content:
            metadata = ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                source_text_position=current_start,
                chunk_size=len(current_content),
                overlap_size=self.overlap if chunks else 0
            )
            chunks.append(Chunk(content=current_content, metadata=metadata))
        
        return chunks
    
    def _chunk_paragraph(self, text: str) -> List[Chunk]:
        """段落邊界分塊"""
        # 使用換行符分割段落
        paragraphs = re.split(r'\\n\\s*\\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if not paragraphs:
            return self._chunk_fixed(text)
        
        chunks = []
        current_content = ""
        current_start = 0
        position = 0
        
        for paragraph in paragraphs:
            paragraph_with_newline = paragraph + "\\n\\n"
            
            # 如果單個段落超過 chunk_size，使用固定分塊處理
            if len(paragraph) > self.chunk_size:
                # 先保存當前累積的內容
                if current_content:
                    metadata = ChunkMetadata(
                        chunk_id=str(uuid.uuid4()),
                        source_text_position=current_start,
                        chunk_size=len(current_content),
                        overlap_size=self.overlap if chunks else 0
                    )
                    chunks.append(Chunk(content=current_content.strip(), metadata=metadata))
                    current_content = ""
                
                # 對長段落使用固定分塊
                sub_chunker = TextChunker(
                    chunk_size=self.chunk_size,
                    overlap=self.overlap,
                    strategy="fixed"
                )
                sub_chunks = sub_chunker._chunk_fixed(paragraph)
                
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata.source_text_position += position
                    chunks.append(sub_chunk)
                
                position += len(paragraph_with_newline)
                current_start = position
                continue
            
            # 如果添加這個段落會超過 chunk_size
            if len(current_content) + len(paragraph_with_newline) > self.chunk_size and current_content:
                stripped_content = current_content.strip()
                metadata = ChunkMetadata(
                    chunk_id=str(uuid.uuid4()),
                    source_text_position=current_start,
                    chunk_size=len(stripped_content),
                    overlap_size=self.overlap if chunks else 0
                )
                chunks.append(Chunk(content=stripped_content, metadata=metadata))
                
                # 計算重疊部分
                overlap_content = stripped_content[-self.overlap:] if self.overlap > 0 else ""
                # 更新 current_start，因為我們改變了重疊內容的來源
                # 注意：這裡的計算比較複雜，因為我們使用了 stripped_content
                # 簡單起見，我們重置 start 為當前位置減去重疊長度
                current_start = position - len(overlap_content)
                current_content = overlap_content + paragraph_with_newline
            else:
                current_content += paragraph_with_newline
            
            position += len(paragraph_with_newline)
        
        # 處理最後一個 chunk
        if current_content:
            metadata = ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                source_text_position=current_start,
                chunk_size=len(current_content.strip()),
                overlap_size=self.overlap if chunks else 0
            )
            chunks.append(Chunk(content=current_content.strip(), metadata=metadata))
        
        return chunks
    
    def _set_overlap_info(self, chunks: List[Chunk]) -> None:
        """設置 chunks 之間的重疊信息"""
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.metadata.overlap_before = chunks[i - 1].metadata.chunk_id
                # 設置重疊大小（如果還沒設置）
                if chunk.metadata.overlap_size == 0:
                    chunk.metadata.overlap_size = self.overlap
            if i < len(chunks) - 1:
                chunk.metadata.overlap_after = chunks[i + 1].metadata.chunk_id
    
    def log_chunking_info(self, message: str) -> None:
        """輸出中文分塊日誌"""
        logger.info(message)