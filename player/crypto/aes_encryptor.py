# player/crypto/aes_encryptor.py
from typing import Tuple
from Crypto.Cipher import AES
from Crypto.Util import Counter
from .base_encryptor import BaseEncryptor
from ..exceptions.custom_exceptions import CryptoError


class AESEncryptor(BaseEncryptor):
    """AES加密算法实现"""
    
    def __init__(self, mode: str = "CTR", key_size: int = 256):
        """
        初始化AES加密器
        
        Args:
            mode: 加密模式（CTR/CBC）
            key_size: 密钥长度（128/192/256）
        """
        self.mode = mode.upper()
        self.key_size = key_size
        
        # 验证参数
        if self.mode not in ["CTR", "CBC"]:
            raise CryptoError(f"不支持的AES模式: {self.mode}", algorithm="AES")
        
        if key_size not in [128, 192, 256]:
            raise CryptoError(f"不支持的密钥长度: {key_size}", algorithm="AES")
    
    def encrypt(self, data: bytes, key: bytes, **kwargs) -> Tuple[bytes, dict]:
        """
        AES加密
        
        Args:
            data: 待加密数据
            key: 加密密钥
            **kwargs: 额外参数（如iv）
            
        Returns:
            (加密数据, 加密信息)
            
        Raises:
            CryptoError: 加密失败
        """
        try:
            if self.mode == "CTR":
                return self._encrypt_ctr(data, key, kwargs.get('iv'))
            elif self.mode == "CBC":
                return self._encrypt_cbc(data, key, kwargs.get('iv'))
            else:
                raise CryptoError(f"不支持的AES模式: {self.mode}", algorithm="AES")
        except Exception as e:
            raise CryptoError(f"AES加密失败: {e}", algorithm="AES")
    
    def decrypt(self, data: bytes, key: bytes, **kwargs) -> bytes:
        """
        AES解密
        
        Args:
            data: 待解密数据
            key: 解密密钥
            **kwargs: 额外参数（如iv）
            
        Returns:
            解密数据
            
        Raises:
            CryptoError: 解密失败
        """
        try:
            if self.mode == "CTR":
                return self._decrypt_ctr(data, key, kwargs.get('iv'))
            elif self.mode == "CBC":
                return self._decrypt_cbc(data, key, kwargs.get('iv'))
            else:
                raise CryptoError(f"不支持的AES模式: {self.mode}", algorithm="AES")
        except Exception as e:
            raise CryptoError(f"AES解密失败: {e}", algorithm="AES")
    
    def _encrypt_ctr(self, data: bytes, key: bytes, iv: bytes = None) -> Tuple[bytes, dict]:
        """CTR模式加密"""
        if iv is None:
            import os
            iv = os.urandom(16)  # 生成16字节随机nonce/IV
        
        # 创建计数器
        counter = Counter.new(64, prefix=iv[:8], initial_value=int.from_bytes(iv[8:], 'big'))
        
        # 创建加密器
        cipher = AES.new(key, AES.MODE_CTR, counter=counter)
        encrypted = cipher.encrypt(data)
        
        return encrypted, {'iv': iv}
    
    def _decrypt_ctr(self, data: bytes, key: bytes, iv: bytes = None) -> bytes:
        """CTR模式解密"""
        if iv is None:
            raise CryptoError("CTR模式解密需要IV参数", algorithm="AES-CTR")
        
        # 创建计数器
        counter = Counter.new(64, prefix=iv[:8], initial_value=int.from_bytes(iv[8:], 'big'))
        
        # 创建解密器
        cipher = AES.new(key, AES.MODE_CTR, counter=counter)
        return cipher.decrypt(data)
    
    def _encrypt_cbc(self, data: bytes, key: bytes, iv: bytes = None) -> Tuple[bytes, dict]:
        """CBC模式加密"""
        if iv is None:
            import os
            iv = os.urandom(16)  # 生成16字节随机IV
        
        # 创建加密器
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # PKCS7填充
        padding_length = 16 - len(data) % 16
        padding = bytes([padding_length] * padding_length)
        data_to_encrypt = data + padding
        
        encrypted = cipher.encrypt(data_to_encrypt)
        return encrypted, {'iv': iv}
    
    def _decrypt_cbc(self, data: bytes, key: bytes, iv: bytes = None) -> bytes:
        """CBC模式解密"""
        if iv is None:
            raise CryptoError("CBC模式解密需要IV参数", algorithm="AES-CBC")
        
        # 创建解密器
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(data)
        
        # 去除PKCS7填充
        padding_length = decrypted[-1]
        return decrypted[:-padding_length]
    
    def get_algorithm_name(self) -> str:
        """获取算法名称"""
        return f"AES-{self.mode}"
