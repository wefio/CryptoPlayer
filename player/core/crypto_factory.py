# player/core/crypto_factory.py
from typing import Dict, List
from ..crypto.base_encryptor import BaseEncryptor
from ..crypto.aes_encryptor import AESEncryptor
from ..crypto.chacha20_encryptor import ChaCha20Encryptor
from ..exceptions.custom_exceptions import CryptoError


class CryptoAlgorithmFactory:
    """加密算法工厂"""
    
    def __init__(self):
        """初始化算法工厂"""
        self._algorithms: Dict[str, type] = {
            "AES-CTR": AESEncryptor,
            "AES-CBC": AESEncryptor,
            "ChaCha20": ChaCha20Encryptor
        }
    
    def create_algorithm(self, algorithm_name: str, **kwargs) -> BaseEncryptor:
        """
        创建加密算法实例
        
        Args:
            algorithm_name: 算法名称
            **kwargs: 算法特定参数
            
        Returns:
            加密算法实例
            
        Raises:
            CryptoError: 算法不支持或创建失败
        """
        if algorithm_name not in self._algorithms:
            raise CryptoError(f"不支持的加密算法: {algorithm_name}")
        
        try:
            if algorithm_name.startswith("AES-"):
                mode = algorithm_name.split("-")[1]
                return self._algorithms[algorithm_name](mode=mode, **kwargs)
            else:
                return self._algorithms[algorithm_name](**kwargs)
        except Exception as e:
            raise CryptoError(f"创建算法实例失败: {e}", algorithm=algorithm_name)
    
    def get_available_algorithms(self) -> List[str]:
        """
        获取可用算法列表
        
        Returns:
            支持的算法名称列表
        """
        return list(self._algorithms.keys())
    
    def get_algorithm_info(self, algorithm_name: str) -> Dict:
        """
        获取算法信息
        
        Args:
            algorithm_name: 算法名称
            
        Returns:
            算法信息字典
        """
        info_map = {
            "AES-CTR": {
                "description": "AES-CTR加密，流式加密模式",
                "security": "高",
                "performance": "高",
                "recommended": True
            },
            "AES-CBC": {
                "description": "AES-CBC加密，需要填充",
                "security": "高",
                "performance": "中",
                "recommended": False
            },
            "ChaCha20": {
                "description": "ChaCha20流加密，移动设备性能好",
                "security": "高",
                "performance": "高",
                "recommended": True
            }
        }
        
        return info_map.get(algorithm_name, {})