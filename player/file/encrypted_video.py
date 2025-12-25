# player/file/encrypted_video.py
import os
from typing import Optional, Tuple
from .file_header import FileHeader
from ..exceptions.custom_exceptions import FileFormatError
from ..utils.file_utils import FileUtils


class EncryptedVideoFile:
    """加密视频文件"""
    
    def __init__(self, file_path: str = None):
        """
        初始化加密视频文件
        
        Args:
            file_path: 文件路径
        """
        self.file_path = file_path
        self.header: Optional[FileHeader] = None
        self.notice_data: Optional[bytes] = None
        self.encrypted_data: Optional[bytes] = None
        self.file_size: int = 0
        
        if file_path:
            self.load_file()
    
    def load_file(self) -> bool:
        """
        加载并解析文件
        
        文件结构：
        1. 提示段（完整MP4文件，通用播放器可播放）
        2. 文件头（包含加密信息和加密数据大小）
        3. 加密视频流数据
        
        Returns:
            是否成功
            
        Raises:
            FileFormatError: 文件格式错误
        """
        if not self.file_path or not os.path.exists(self.file_path):
            raise FileFormatError(f"文件不存在: {self.file_path}")
        
        try:
            self.file_size = os.path.getsize(self.file_path)
            
            with open(self.file_path, 'rb') as f:
                # 读取整个文件到内存（用于搜索文件头位置）
                file_data = f.read()
            
            # 搜索文件头魔数"ENCV"的位置
            magic_bytes = b'ENCV'
            header_pos = file_data.find(magic_bytes)
            
            if header_pos == -1:
                raise FileFormatError("找不到有效的文件头标记")
            
            # 提取提示段（文件头之前的所有数据）
            self.notice_data = file_data[:header_pos]
            
            # 读取文件头
            header_data = file_data[header_pos:header_pos + FileHeader.HEADER_SIZE]
            self.header = FileHeader.from_bytes(header_data)
            
            # 读取加密数据
            encrypted_data_start = header_pos + FileHeader.HEADER_SIZE
            self.encrypted_data = file_data[encrypted_data_start:]
            
            # 验证加密数据大小
            if self.header.encrypted_size > 0 and len(self.encrypted_data) != self.header.encrypted_size:
                raise FileFormatError(
                    f"加密数据大小不匹配: 期望 {self.header.encrypted_size}, 实际 {len(self.encrypted_data)}"
                )
            
            return True
        except Exception as e:
            raise FileFormatError(f"加载文件失败: {e}")
    
    def save_file(self, output_path: str) -> bool:
        """
        保存文件
        
        文件结构：
        1. 提示段（完整MP4文件，通用播放器可播放）
        2. 文件头（包含加密信息和加密数据大小）
        3. 加密视频流数据
        
        Args:
            output_path: 输出路径
            
        Returns:
            是否成功
        """
        if not self.header:
            raise FileFormatError("没有文件头，无法保存")
        
        try:
            # 更新加密数据大小
            if self.encrypted_data:
                self.header.encrypted_size = len(self.encrypted_data)
            
            # 构建文件数据：提示段 + 文件头 + 加密数据
            file_data = b''
            if self.notice_data:
                file_data += self.notice_data
            file_data += self.header.to_bytes()
            if self.encrypted_data:
                file_data += self.encrypted_data
            
            return FileUtils.write_file_safe(output_path, file_data)
        except Exception as e:
            raise FileFormatError(f"保存文件失败: {e}")
    
    def create_from_parts(self, notice_data: bytes, encrypted_data: bytes, 
                         header: FileHeader) -> 'EncryptedVideoFile':
        """
        从各部分创建加密视频文件
        
        Args:
            notice_data: 提示段数据（完整的MP4文件）
            encrypted_data: 加密数据
            header: 文件头
            
        Returns:
            自身实例（用于链式调用）
        """
        self.notice_data = notice_data
        self.encrypted_data = encrypted_data
        self.header = header
        
        # 更新文件头中的加密数据大小
        if self.header and encrypted_data:
            self.header.encrypted_size = len(encrypted_data)
        
        return self
    
    def extract_notice_section(self) -> Optional[bytes]:
        """
        提取提示段
        
        Returns:
            提示段数据
        """
        return self.notice_data
    
    def extract_encrypted_section(self) -> Optional[bytes]:
        """
        提取加密段
        
        Returns:
            加密数据
        """
        return self.encrypted_data
    
    def get_notice_temp_file(self) -> Optional[str]:
        """
        获取提示段的临时文件路径
        
        Returns:
            临时文件路径
        """
        if not self.notice_data:
            return None
        
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_file.write(self.notice_data)
        temp_file.close()
        return temp_file.name
    
    def verify_integrity(self) -> Tuple[bool, str]:
        """
        验证文件完整性
        
        Returns:
            (是否完整, 错误信息)
        """
        if not self.header:
            return False, "缺少文件头"
        
        notice_size = len(self.notice_data) if self.notice_data else 0
        encrypted_size = len(self.encrypted_data) if self.encrypted_data else 0
        expected_size = notice_size + FileHeader.HEADER_SIZE + encrypted_size
        
        if expected_size > 0 and self.file_size != expected_size:
            return False, f"文件大小不匹配: 期望 {expected_size}, 实际 {self.file_size}"
        
        # 验证加密数据大小是否与文件头中记录的一致
        if self.header.encrypted_size > 0 and encrypted_size != self.header.encrypted_size:
            return False, f"加密数据大小不匹配: 文件头记录 {self.header.encrypted_size}, 实际 {encrypted_size}"
        
        return True, "文件完整"
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.header:
            notice_size = len(self.notice_data) if self.notice_data else 0
            encrypted_size = len(self.encrypted_data) if self.encrypted_data else 0
            return (f"EncryptedVideoFile(notice={notice_size} bytes, "
                    f"encrypted={encrypted_size} bytes, header={self.header})")
        return "EncryptedVideoFile(未加载)"
