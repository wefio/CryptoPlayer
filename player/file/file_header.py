# player/file/file_header.py
import struct
from typing import Dict, Any
from ..exceptions.custom_exceptions import FileFormatError


class FileHeader:
    """加密文件头（位于提示段之后）"""
    
    FORMAT = '4s B Q 64s'  # magic(4), version(1), encrypted_size(8), reserved(64)
    HEADER_SIZE = struct.calcsize(FORMAT)
    
    def __init__(self, magic: bytes = b'ENCV', version: int = 1, 
                 encrypted_size: int = 0, reserved: bytes = b''):
        """
        初始化文件头
        
        Args:
            magic: 魔数
            version: 版本号
            encrypted_size: 加密数据大小
            reserved: 预留字段
        """
        self.magic = magic
        self.version = version
        self.encrypted_size = encrypted_size
        
        # 确保reserved长度为64字节
        if len(reserved) < 64:
            reserved = reserved + b'\x00' * (64 - len(reserved))
        elif len(reserved) > 64:
            reserved = reserved[:64]
        self.reserved = reserved
        
        # 加密信息（存储在reserved中）
        self.encryption_info = {}
    
    def to_bytes(self) -> bytes:
        """
        转换为字节
        
        Returns:
            字节表示
        """
        return struct.pack(self.FORMAT, 
                          self.magic, 
                          self.version, 
                          self.encrypted_size, 
                          self.reserved)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'FileHeader':
        """
        从字节解析文件头
        
        Args:
            data: 字节数据
            
        Returns:
            FileHeader实例
            
        Raises:
            FileFormatError: 数据长度不足或解析失败
        """
        if len(data) < cls.HEADER_SIZE:
            raise FileFormatError("文件头数据长度不足")
        
        try:
            magic, version, encrypted_size, reserved = struct.unpack(cls.FORMAT, data[:cls.HEADER_SIZE])
            
            # 验证魔数
            if magic != b'ENCV':
                raise FileFormatError(
                    f"无效的文件格式，期望 'ENCV'，实际 '{magic.decode('ascii', errors='replace')}'",
                    expected_format="ENCV",
                    actual_format=magic.decode('ascii', errors='replace')
                )
            
            return cls(magic, version, encrypted_size, reserved)
        except struct.error as e:
            raise FileFormatError(f"解析文件头失败: {e}")
    
    def set_encryption_info(self, algorithm: str, salt: bytes, iv_nonce: bytes):
        """
        设置加密信息到reserved字段
        
        Args:
            algorithm: 加密算法
            salt: 盐值
            iv_nonce: IV/Nonce
        """
        # 简单编码：algorithm(16) + salt_len(1) + salt + iv_len(1) + iv
        algorithm_bytes = algorithm.encode('utf-8').ljust(16, b'\x00')
        salt_len = len(salt)
        iv_len = len(iv_nonce)
        
        info_data = algorithm_bytes + bytes([salt_len]) + salt + bytes([iv_len]) + iv_nonce
        
        # 确保不超过64字节
        if len(info_data) > 64:
            info_data = info_data[:64]
        
        self.reserved = info_data.ljust(64, b'\x00')
    
    def get_encryption_info(self) -> Dict[str, Any]:
        """
        从reserved字段提取加密信息
        
        Returns:
            加密信息字典
        """
        if len(self.reserved) < 64:
            return {}
        
        algorithm_bytes = self.reserved[:16].rstrip(b'\x00')
        salt_len = self.reserved[16]
        
        if salt_len > 0 and 17 + salt_len <= 64:
            salt = self.reserved[17:17+salt_len]
            iv_start = 17 + salt_len
            iv_len = self.reserved[iv_start] if iv_start < 64 else 0
            iv = self.reserved[iv_start+1:iv_start+1+iv_len] if iv_len > 0 else b''
            
            return {
                'algorithm': algorithm_bytes.decode('utf-8', errors='ignore'),
                'salt': salt,
                'iv_nonce': iv
            }
        
        return {}
    
    def __str__(self) -> str:
        """字符串表示"""
        info = self.get_encryption_info()
        return (f"FileHeader(magic={self.magic}, version={self.version}, "
                f"encrypted_size={self.encrypted_size}, algorithm={info.get('algorithm', 'N/A')})")
