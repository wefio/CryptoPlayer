# player/core/decryptor.py
import tempfile
from typing import Optional, Dict, Any
from ..crypto.base_encryptor import BaseEncryptor
from ..file.encrypted_video import EncryptedVideoFile
from ..ffmpeg.ffmpeg_wrapper import FFmpegWrapper
from ..exceptions.custom_exceptions import CryptoError, PasswordError, FileFormatError
from ..utils.file_utils import FileUtils


class Decryptor:
    """解密器"""

    def __init__(self, algorithm: str = "AES-CTR"):
        """
        初始化解密器

        Args:
            algorithm: 解密算法名称
        """
        self.algorithm = algorithm
        self.crypto_algorithm: Optional[BaseEncryptor] = None
        self._init_crypto_algorithm()

    def _init_crypto_algorithm(self):
        """初始化解密算法"""
        from .crypto_factory import CryptoAlgorithmFactory
        factory = CryptoAlgorithmFactory()
        self.crypto_algorithm = factory.create_algorithm(self.algorithm)

    def parse_file_header(self, file_path: str) -> Dict[str, Any]:
        """
        解析加密文件头

        Args:
            file_path: 加密文件路径

        Returns:
            文件头信息字典

        Raises:
            FileFormatError: 文件格式错误
        """
        try:
            encrypted_file = EncryptedVideoFile(file_path)
            header_info = {
                'magic': encrypted_file.header.magic,
                'version': encrypted_file.header.version,
                'encryption_info': encrypted_file.header.get_encryption_info()
            }
            return header_info
        except Exception as e:
            raise FileFormatError(f"解析文件头失败: {e}")

    def decrypt_stream(self, encrypted_data: bytes, password: str,
                       encryption_info: Dict[str, Any]) -> bytes:
        """
        解密视频流

        Args:
            encrypted_data: 加密数据
            password: 解密密码
            encryption_info: 加密信息（包含算法、salt、iv_nonce等）

        Returns:
            解密后的数据

        Raises:
            PasswordError: 密码错误
            CryptoError: 解密失败
        """
        if not self.crypto_algorithm:
            raise CryptoError("解密算法未初始化")

        try:
            # 从加密信息中获取算法、salt和iv/nonce
            algorithm = encryption_info.get('algorithm', self.algorithm)
            salt = encryption_info.get('salt')
            iv_nonce = encryption_info.get('iv_nonce')

            # 如果算法不匹配，重新初始化算法
            if algorithm != self.algorithm:
                from .crypto_factory import CryptoAlgorithmFactory
                factory = CryptoAlgorithmFactory()
                self.crypto_algorithm = factory.create_algorithm(algorithm)
                self.algorithm = algorithm

            # 生成密钥
            key, _ = self.crypto_algorithm.generate_key(password, salt)

            # 解密数据
            if algorithm.startswith('AES'):
                if iv_nonce is None or len(iv_nonce) == 0:
                    raise CryptoError("解密失败：缺少IV参数", algorithm=algorithm)
                decrypted_data = self.crypto_algorithm.decrypt(encrypted_data, key, iv=iv_nonce)
            elif algorithm == 'ChaCha20':
                if iv_nonce is None or len(iv_nonce) == 0:
                    raise CryptoError("解密失败：缺少Nonce参数", algorithm=algorithm)
                decrypted_data = self.crypto_algorithm.decrypt(encrypted_data, key, nonce=iv_nonce)
            else:
                raise CryptoError(f"不支持的算法: {algorithm}")

            return decrypted_data

        except Exception as e:
            if "decrypt" in str(e).lower() or "password" in str(e).lower():
                raise PasswordError("解密失败，密码可能错误", remaining_attempts=3)
            else:
                raise CryptoError(f"解密失败: {e}", algorithm=algorithm)

    def decrypt_to_temp_file(self, encrypted_file_path: str, password: str) -> str:
        """
        解密视频流到临时文件

        Args:
            encrypted_file_path: 加密文件路径
            password: 解密密码

        Returns:
            临时文件路径

        Raises:
            FileFormatError: 文件格式错误
            PasswordError: 密码错误
            CryptoError: 解密失败
        """
        try:
            # 加载加密文件
            encrypted_file = EncryptedVideoFile(encrypted_file_path)

            # 获取加密信息
            encryption_info = encrypted_file.header.get_encryption_info()

            # 解密视频流
            encrypted_data = encrypted_file.extract_encrypted_section()
            if not encrypted_data:
                raise CryptoError("没有加密数据")

            decrypted_data = self.decrypt_stream(encrypted_data, password, encryption_info)

            # 将解密后的数据写入临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_file.write(decrypted_data)
            temp_file.close()

            return temp_file.name

        except Exception as e:
            if isinstance(e, (FileFormatError, PasswordError, CryptoError)):
                raise e
            else:
                raise CryptoError(f"解密到临时文件失败: {e}")
