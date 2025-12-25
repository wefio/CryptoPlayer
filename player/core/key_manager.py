# player/core/key_manager.py
import os
import hashlib
from typing import Tuple, Optional
from ..exceptions.custom_exceptions import PasswordError


class KeyManager:
    """密钥管理器"""
    
    def __init__(self, key_derivation_func: str = "PBKDF2", 
                 key_storage_path: Optional[str] = None):
        """
        初始化密钥管理器
        
        Args:
            key_derivation_func: 密钥派生函数
            key_storage_path: 密钥存储路径（仅用于测试）
        """
        self.key_derivation_func = key_derivation_func
        self.key_storage_path = key_storage_path
    
    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None,
                                 algorithm: Optional[str] = None,
                                 iterations: int = 100000) -> Tuple[bytes, bytes]:
        """
        从密码派生密钥
        
        Args:
            password: 密码
            salt: 盐值
            algorithm: 派生算法（默认使用实例配置）
            iterations: 迭代次数
            
        Returns:
            (密钥, salt)
        """
        if algorithm is None:
            algorithm = self.key_derivation_func
        
        if salt is None:
            salt = os.urandom(16)
        
        try:
            if algorithm == "PBKDF2":
                key = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode('utf-8'),
                    salt,
                    iterations,
                    dklen=32
                )
            else:
                raise PasswordError(f"不支持的密钥派生算法: {algorithm}")
            
            # 保存密钥信息（仅用于调试）
            if self.key_storage_path:
                self._save_key_info_debug(key, salt)
            
            return key, salt
        except Exception as e:
            raise PasswordError(f"密钥派生失败: {e}")
    
    def validate_password(self, password: str, stored_hash: bytes, salt: bytes) -> bool:
        """
        验证密码
        
        Args:
            password: 待验证密码
            stored_hash: 存储的哈希值
            salt: 盐值
            
        Returns:
            密码是否正确
        """
        # 重新计算哈希
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000,
            dklen=32
        )
        
        # 使用恒定时间比较防止时序攻击
        return self._constant_time_compare(password_hash, stored_hash)
    
    def save_key_info(self, key_info: dict, file_path: str) -> bool:
        """
        保存密钥信息（仅用于调试）
        
        Args:
            key_info: 密钥信息字典
            file_path: 保存路径
            
        Returns:
            是否成功
        """
        import json
        
        try:
            # 安全处理：不保存实际密钥
            safe_info = {
                'algorithm': key_info.get('algorithm'),
                'salt_hex': key_info.get('salt', b'').hex() if key_info.get('salt') else None,
                'iterations': key_info.get('iterations')
            }
            
            with open(file_path, 'w') as f:
                json.dump(safe_info, f, indent=2)
            
            print(f"警告：密钥信息已保存到 {file_path}（仅用于调试）")
            return True
        except Exception as e:
            print(f"保存密钥信息失败: {e}")
            return False
    
    def _save_key_info_debug(self, key: bytes, salt: bytes):
        """调试用：保存密钥信息"""
        if self.key_storage_path:
            key_info = {
                'key_hash': hashlib.sha256(key).hexdigest(),
                'salt_hex': salt.hex(),
                'algorithm': self.key_derivation_func
            }
            self.save_key_info(key_info, self.key_storage_path)
    
    @staticmethod
    def _constant_time_compare(a: bytes, b: bytes) -> bool:
        """恒定时间比较（防止时序攻击）"""
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= x ^ y
        return result == 0