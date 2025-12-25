# player/utils/file_utils.py
import os
import hashlib
from typing import Generator, Optional
from pathlib import Path


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def read_file_chunks(file_path: str, chunk_size: int = 8192) -> Generator[bytes, None, None]:
        """
        分块读取大文件
        
        Args:
            file_path: 文件路径
            chunk_size: 块大小
            
        Yields:
            数据块
        """
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法
            
        Returns:
            文件的哈希值
        """
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    
    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """
        确保目录存在
        
        Args:
            directory: 目录路径
            
        Returns:
            是否成功
        """
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节），失败返回None
        """
        try:
            return os.path.getsize(file_path)
        except OSError:
            return None
    
    @staticmethod
    def write_file_safe(file_path: str, data: bytes, mode: str = 'wb') -> bool:
        """
        安全写入文件（先写入临时文件，再重命名）
        
        Args:
            file_path: 目标文件路径
            data: 要写入的数据
            mode: 写入模式
            
        Returns:
            是否成功
        """
        temp_path = f"{file_path}.tmp"
        try:
            with open(temp_path, mode) as f:
                f.write(data)
            os.replace(temp_path, file_path)
            return True
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False