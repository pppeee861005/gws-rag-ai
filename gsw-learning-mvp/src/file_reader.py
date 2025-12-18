# -*- coding: utf-8 -*-
"""
文件讀取器模組 (File Reader Module)

支持多種文本格式的文件讀取，使用 UTF-8 編碼正確處理中文內容，
提供文件元數據和錯誤處理功能。

需求：0.1, 0.2, 0.3, 0.4, 0.5
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime

# 配置中文日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("文件讀取器")


@dataclass
class FileMetadata:
    """文件元數據"""
    file_path: str
    file_size: int
    encoding: str
    file_extension: str
    last_modified: datetime
    is_readable: bool
    content_type: str


class FileReader:
    """
    文件讀取器 - 支持多種文本格式的文件讀取
    
    支持的文件格式：
    - .txt: 純文本文件
    - .md: Markdown 文件
    - .json: JSON 文件
    
    特性：
    - UTF-8 編碼處理中文內容
    - 文件元數據提取
    - 錯誤處理和中文錯誤提示
    - 中文日誌輸出
    
    需求：0.1, 0.2, 0.3, 0.4, 0.5
    """
    
    # 支持的文件格式
    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.json'}
    
    def __init__(self, encoding: str = 'utf-8'):
        """
        初始化文件讀取器
        
        Args:
            encoding: 文件編碼格式，默認為 UTF-8
        """
        self.encoding = encoding
        self.log_info("文件讀取器初始化完成，使用編碼: {}".format(encoding))
    
    def read_file(self, file_path: Union[str, Path]) -> Dict:
        """
        讀取文件內容和元數據
        
        Args:
            file_path: 文件路徑（字符串或 Path 對象）
        
        Returns:
            Dict: 包含文件內容和元數據的字典：
                - content: 文件內容
                - metadata: 文件元數據對象
                - success: 讀取是否成功
                - error_message: 錯誤信息（如果有）
        """
        # 轉換為 Path 對象
        path = Path(file_path)
        
        self.log_info(f"開始讀取文件: {path}")
        
        try:
            # 檢查文件是否存在
            if not path.exists():
                error_msg = f"文件不存在: {path}"
                self.log_error(error_msg)
                return {
                    'content': None,
                    'metadata': None,
                    'success': False,
                    'error_message': error_msg
                }
            
            # 檢查是否為文件（而非目錄）
            if not path.is_file():
                error_msg = f"指定路徑不是文件: {path}"
                self.log_error(error_msg)
                return {
                    'content': None,
                    'metadata': None,
                    'success': False,
                    'error_message': error_msg
                }
            
            # 檢查文件格式是否支持
            file_extension = path.suffix.lower()
            if file_extension not in self.SUPPORTED_EXTENSIONS:
                error_msg = f"不支持的文件格式: {file_extension}。支持的格式: {', '.join(self.SUPPORTED_EXTENSIONS)}"
                self.log_error(error_msg)
                return {
                    'content': None,
                    'metadata': None,
                    'success': False,
                    'error_message': error_msg
                }
            
            # 獲取文件元數據
            metadata = self._get_file_metadata(path)
            
            # 讀取文件內容
            content = self._read_file_content(path, file_extension)
            
            self.log_info(f"文件讀取成功: {path}，內容長度: {len(content) if content else 0} 字符")
            
            return {
                'content': content,
                'metadata': metadata,
                'success': True,
                'error_message': None
            }
            
        except PermissionError:
            error_msg = f"沒有權限讀取文件: {path}"
            self.log_error(error_msg)
            return {
                'content': None,
                'metadata': None,
                'success': False,
                'error_message': error_msg
            }
        except UnicodeDecodeError as e:
            error_msg = f"文件編碼錯誤，無法使用 {self.encoding} 編碼讀取文件 {path}: {str(e)}"
            self.log_error(error_msg)
            return {
                'content': None,
                'metadata': None,
                'success': False,
                'error_message': error_msg
            }
        except Exception as e:
            error_msg = f"讀取文件時發生未知錯誤 {path}: {str(e)}"
            self.log_error(error_msg)
            return {
                'content': None,
                'metadata': None,
                'success': False,
                'error_message': error_msg
            }
    
    def _get_file_metadata(self, path: Path) -> FileMetadata:
        """
        獲取文件元數據
        
        Args:
            path: 文件路徑
        
        Returns:
            FileMetadata: 文件元數據對象
        """
        try:
            stat = path.stat()
            file_extension = path.suffix.lower()
            
            # 確定內容類型
            content_type_map = {
                '.txt': 'text/plain',
                '.md': 'text/markdown',
                '.json': 'application/json'
            }
            content_type = content_type_map.get(file_extension, 'text/plain')
            
            # 檢查文件是否可讀
            is_readable = os.access(path, os.R_OK)
            
            metadata = FileMetadata(
                file_path=str(path.absolute()),
                file_size=stat.st_size,
                encoding=self.encoding,
                file_extension=file_extension,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                is_readable=is_readable,
                content_type=content_type
            )
            
            self.log_info(f"文件元數據獲取成功: {path.name}，大小: {stat.st_size} 字節")
            return metadata
            
        except Exception as e:
            self.log_error(f"獲取文件元數據失敗 {path}: {str(e)}")
            raise
    
    def _read_file_content(self, path: Path, file_extension: str) -> str:
        """
        根據文件類型讀取文件內容
        
        Args:
            path: 文件路徑
            file_extension: 文件擴展名
        
        Returns:
            str: 文件內容
        """
        try:
            if file_extension == '.json':
                # JSON 文件需要特殊處理，確保格式正確
                with open(path, 'r', encoding=self.encoding) as f:
                    json_data = json.load(f)
                # 將 JSON 對象轉換為格式化的字符串
                content = json.dumps(json_data, ensure_ascii=False, indent=2)
                self.log_info(f"JSON 文件讀取並格式化成功: {path.name}")
            else:
                # 文本文件（.txt, .md）直接讀取
                with open(path, 'r', encoding=self.encoding) as f:
                    content = f.read()
                self.log_info(f"文本文件讀取成功: {path.name}")
            
            return content
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON 文件格式錯誤 {path}: {str(e)}"
            self.log_error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            self.log_error(f"讀取文件內容失敗 {path}: {str(e)}")
            raise
    
    def get_supported_extensions(self) -> set:
        """
        獲取支持的文件擴展名
        
        Returns:
            set: 支持的文件擴展名集合
        """
        return self.SUPPORTED_EXTENSIONS.copy()
    
    def is_supported_file(self, file_path: Union[str, Path]) -> bool:
        """
        檢查文件是否為支持的格式
        
        Args:
            file_path: 文件路徑
        
        Returns:
            bool: 是否支持該文件格式
        """
        path = Path(file_path)
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def log_info(self, message: str) -> None:
        """輸出中文信息日誌"""
        logger.info(message)
    
    def log_error(self, message: str) -> None:
        """輸出中文錯誤日誌"""
        logger.error(message)
    
    def log_warning(self, message: str) -> None:
        """輸出中文警告日誌"""
        logger.warning(message)


# 便利函數
def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> Dict:
    """
    便利函數：讀取文本文件
    
    Args:
        file_path: 文件路徑
        encoding: 編碼格式，默認 UTF-8
    
    Returns:
        Dict: 文件讀取結果
    """
    reader = FileReader(encoding=encoding)
    return reader.read_file(file_path)


def create_sample_files_for_testing():
    """
    創建測試用的示例文件
    這個函數用於測試目的，創建不同格式的示例文件
    """
    # 創建測試目錄
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # 創建 .txt 文件
    txt_content = """這是一個測試文本文件。
包含中文內容，用於測試 UTF-8 編碼處理。

This is a test text file.
It contains both Chinese and English content.
用於驗證文件讀取器的功能。"""
    
    with open(test_dir / "test.txt", 'w', encoding='utf-8') as f:
        f.write(txt_content)
    
    # 創建 .md 文件
    md_content = """# 測試 Markdown 文件

這是一個測試用的 Markdown 文件。

## 功能測試

- 支持中文內容
- 支持 **粗體** 和 *斜體*
- 支持代碼塊

```python
def hello():
    print("你好，世界！")
```

## 結論

文件讀取器應該能夠正確處理這個 Markdown 文件。
"""
    
    with open(test_dir / "test.md", 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    # 創建 .json 文件
    json_data = {
        "name": "測試 JSON 文件",
        "description": "用於測試文件讀取器的 JSON 文件",
        "features": [
            "支持中文字符",
            "UTF-8 編碼",
            "結構化數據"
        ],
        "metadata": {
            "version": "1.0",
            "author": "GSW 學習系統",
            "created": "2024-01-01"
        }
    }
    
    with open(test_dir / "test.json", 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"測試文件已創建在 {test_dir} 目錄中")