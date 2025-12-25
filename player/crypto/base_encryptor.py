# player/crypto/base_encryptor.py
from abc import ABC, abstractmethod
from typing import Tuple, Optional
import hashlib
import os
from ..exceptions.custom_exceptions import CryptoError


class BaseEncryptor(ABC):
    """加密算法基类（抽象类）"""
    
    @abstractmethod
    def encrypt(self, data: bytes, key: bytes, **kwargs) -> Tuple[bytes, dict]:
        """
        加密数据
        
        Args:
            data: 待加密数据
            key: 加密密钥
            **kwargs: 算法特定参数
            
        Returns:
            (加密数据, 额外参数如IV)
        """
        pass
    
    @abstractmethod
    def decrypt(self, data: bytes, key: bytes, **kwargs) -> bytes:
        """
        解密数据
        
        Args:
            data: 待解密数据
            key: 解密密钥
            **kwargs: 算法特定参数
            
        Returns:
            解密数据
        """
        pass
    
    def generate_key(self, password: str, salt: Optional[bytes] = None, 
                    algorithm: str = "PBKDF2", iterations: int = 100000) -> Tuple[bytes, bytes]:
        """
        从密码派生密钥
        
        Args:
            password: 密码
            salt: 盐值，如果为None则生成随机盐
            algorithm: 密钥派生算法
            iterations: 迭代次数
            
        Returns:
            (密钥, salt)
            
        Raises:
            CryptoError: 密钥派生失败
        """
        if salt is None:
            salt = os.urandom(16)
        
        try:
            if algorithm == "PBKDF2":
                # 使用PBKDF2派生密钥
                key = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode('utf-8'),
                    salt,
                    iterations,
                    dklen=32
                )
            elif algorithm == "scrypt":
                # 使用scrypt派生密钥（更安全但更慢）
                import hashlib as hl
                key = hl.scrypt(
                    password.encode('utf-8'),
                    salt=salt,
                    n=2**14,
                    r=8,
                    p=1,
                    dklen=32
                )
            else:
                raise CryptoError(f"不支持的密钥派生算法: {algorithm}", algorithm=algorithm)
            
            return key, salt
        except Exception as e:
            raise CryptoError(f"密钥派生失败: {e}", algorithm=algorithm)
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """获取算法名称"""
        pass