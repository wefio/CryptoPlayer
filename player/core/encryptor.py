# player/core/encryptor.py
import os
from typing import Optional
from ..crypto.base_encryptor import BaseEncryptor
from ..ffmpeg.ffmpeg_wrapper import FFmpegWrapper
from ..file.encrypted_video import EncryptedVideoFile
from ..file.file_header import FileHeader
from ..exceptions.custom_exceptions import CryptoError, FFmpegError
from ..utils.file_utils import FileUtils


class Encryptor:
    """加密器"""

    def __init__(self, algorithm: str = "AES-CTR"):
        """
        初始化加密器

        Args:
            algorithm: 加密算法名称
        """
        self.algorithm = algorithm
        self.crypto_algorithm: Optional[BaseEncryptor] = None
        self.ffmpeg_wrapper = FFmpegWrapper()
        self._init_crypto_algorithm()

    def _init_crypto_algorithm(self):
        """初始化加密算法"""
        from .crypto_factory import CryptoAlgorithmFactory
        factory = CryptoAlgorithmFactory()
        self.crypto_algorithm = factory.create_algorithm(self.algorithm)

    def encrypt_stream(self, stream_data: bytes, password: str) -> tuple:
        """
        加密原始视频流

        Args:
            stream_data: 视频流数据
            password: 加密密码

        Returns:
            (加密后的数据, 加密信息字典)

        Raises:
            CryptoError: 加密失败
        """
        if not self.crypto_algorithm:
            raise CryptoError("加密算法未初始化")

        # 生成密钥
        key, salt = self.crypto_algorithm.generate_key(password)

        # 加密数据
        encrypted_data, params = self.crypto_algorithm.encrypt(stream_data, key)

        # 准备加密信息
        encryption_info = {
            'algorithm': self.algorithm,
            'salt': salt,
            'iv_nonce': params.get('iv') or params.get('nonce')
        }

        return encrypted_data, encryption_info

    def _is_video_file(self, file_path: str) -> bool:
        """
        检测文件是否为视频文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为视频文件
        """
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm']
        ext = os.path.splitext(file_path)[1].lower()
        return ext in video_extensions
    
    def generate_encrypted_file(self, plain_video_path: str, notice_video_path: Optional[str],
                                password: str, output_path: str,
                                metadata_config: Optional[str] = None) -> bool:
        """
        生成完整加密文件

        Args:
            plain_video_path: 原始文件路径（可以是视频或任意文件）
            notice_video_path: 提示视频路径（可选，为None时纯加密无提示段）
            password: 加密密码
            output_path: 输出路径
            metadata_config: 元数据配置文件路径

        Returns:
            是否成功

        Raises:
            CryptoError: 加密失败
            FFmpegError: FFmpeg处理失败
        """
        temp_stream_path = None
        temp_notice_path = None
        notice_data = b''  # 默认空提示段
        try:
            # 0. 如果提供了元数据配置且提供了提示视频，先注入到提示视频
            if metadata_config and os.path.exists(metadata_config) and notice_video_path:
                from ..metadata.metadata_handler import MetadataHandler
                metadata_handler = MetadataHandler()
                metadata = metadata_handler.parse_config_file(metadata_config)
                
                if metadata:
                    # 创建临时文件存储带元数据的提示视频
                    import tempfile
                    temp_notice_path = tempfile.mktemp(suffix='.mp4')
                    metadata_handler.inject_metadata(notice_video_path, metadata, temp_notice_path)
                    notice_video_path = temp_notice_path

            # 1. 读取文件数据（视频文件使用FFmpeg提取，其他文件直接读取）
            import tempfile
            
            if self._is_video_file(plain_video_path):
                # 视频文件：提取视频流
                temp_stream_path = tempfile.mktemp(suffix='.mp4')
                self.ffmpeg_wrapper.extract_video_stream(plain_video_path, temp_stream_path)
                
                with open(temp_stream_path, 'rb') as f:
                    stream_data = f.read()
            else:
                # 非视频文件：直接读取
                with open(plain_video_path, 'rb') as f:
                    stream_data = f.read()

            # 3. 加密视频流
            encrypted_data, encryption_info = self.encrypt_stream(stream_data, password)

            # 4. 读取提示视频数据（如果提供了提示视频）
            if notice_video_path and os.path.exists(notice_video_path):
                with open(notice_video_path, 'rb') as f:
                    notice_data = f.read()

            # 5. 创建文件头并设置加密信息
            from ..file.file_header import FileHeader
            header = FileHeader()
            header.set_encryption_info(
                algorithm=encryption_info['algorithm'],
                salt=encryption_info['salt'],
                iv_nonce=encryption_info['iv_nonce']
            )

            # 6. 创建加密视频文件
            from ..file.encrypted_video import EncryptedVideoFile
            encrypted_file = EncryptedVideoFile()
            encrypted_file.create_from_parts(notice_data, encrypted_data, header)
            encrypted_file.save_file(output_path)

            # 注意：暂时禁用FFmpeg元数据注入，因为它会破坏我们的自定义文件格式
            # 元数据已存储在metadata.txt中，可以在播放时读取
            # 7. 注入元数据（暂时跳过）
            # if metadata_config:
            #     from ..metadata.metadata_handler import MetadataHandler
            #     metadata_handler = MetadataHandler()
            #     metadata = metadata_handler.parse_config_file(metadata_config)
            #     metadata_handler.inject_metadata(output_path, metadata)

            return True

        except Exception as e:
            if isinstance(e, (CryptoError, FFmpegError)):
                raise e
            else:
                raise CryptoError(f"生成加密文件失败: {e}")
        finally:
            # 8. 清理临时文件
            if temp_stream_path and os.path.exists(temp_stream_path):
                os.remove(temp_stream_path)
            if temp_notice_path and os.path.exists(temp_notice_path):
                os.remove(temp_notice_path)
