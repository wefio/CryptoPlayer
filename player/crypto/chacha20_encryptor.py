# player/crypto/chacha20_encryptor.py
from typing import Tuple
from Crypto.Cipher import ChaCha20
from .base_encryptor import BaseEncryptor
from ..exceptions.custom_exceptions import CryptoError


class ChaCha20Encryptor(BaseEncryptor):
    """ChaCha20加密算法实现"""
    
    def __init__(self, rounds: int = 20):
        """
        初始化ChaCha20加密器
        
        Args:
            rounds: 加密轮数
        """
        self.rounds = rounds
    
    def encrypt(self, data: bytes, key: bytes, **kwargs) -> Tuple[bytes, dict]:
        """
        ChaCha20加密
        
        Args:
            data: 待加密数据
            key: 加密密钥
            **kwargs: 额外参数（如nonce）
            
        Returns:
            (加密数据, 加密信息)
            
        Raises:
            CryptoError: 加密失败
        """
        try:
            nonce = kwargs.get('nonce')
            if nonce is None:
                nonce = b'\x00' * 12
            
            cipher = ChaCha20.new(key=key, nonce=nonce)
            encrypted = cipher.encrypt(data)
            
            return encrypted, {'nonce': nonce}
        except Exception as e:
            raise CryptoError(f"ChaCha20加密失败: {e}", algorithm="ChaCha20")
    
    def decrypt(self, data: bytes, key: bytes, **kwargs) -> bytes:
        """
        ChaCha20解密
        
        Args:
            data: 待解密数据
            key: 解密密钥
            **kwargs: 额外参数（如nonce）
            
        Returns:
            解密数据
            
        Raises:
            CryptoError: 解密失败
        """
        try:
            nonce = kwargs.get('nonce')
            if nonce is None:
                raise CryptoError("ChaCha20解密需要nonce参数", algorithm="ChaCha20")
            
            cipher = ChaCha20.new(key=key, nonce=nonce)
            return cipher.decrypt(data)
        except Exception as e:
            raise CryptoError(f"ChaCha20解密失败: {e}", algorithm="ChaCha20")
    
    def get_algorithm_name(self) -> str:
        """获取算法名称"""
        return "ChaCha20"