# player/exceptions/custom_exceptions.py

class VideoEncryptionError(Exception):
    """视频加密相关错误的基类"""
    
    def __init__(self, message: str, error_code: int = 0, component: str = None):
        self.error_code = error_code
        self.error_message = message
        self.component = component
        super().__init__(f"[{component}] {message}" if component else message)


class PasswordError(VideoEncryptionError):
    """密码相关错误"""
    
    def __init__(self, message: str, remaining_attempts: int = 0):
        self.remaining_attempts = remaining_attempts
        super().__init__(message, error_code=1001, component="Password")


class FileFormatError(VideoEncryptionError):
    """文件格式错误"""
    
    def __init__(self, message: str, expected_format: str = None, actual_format: str = None):
        self.expected_format = expected_format
        self.actual_format = actual_format
        super().__init__(message, error_code=2001, component="FileFormat")


class MetadataError(VideoEncryptionError):
    """元数据相关错误"""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, error_code=3001, component="Metadata")


class CryptoError(VideoEncryptionError):
    """加密算法错误"""
    
    def __init__(self, message: str, algorithm: str = None):
        self.algorithm = algorithm
        super().__init__(message, error_code=4001, component="Crypto")


class FFmpegError(VideoEncryptionError):
    """FFmpeg相关错误"""
    
    def __init__(self, message: str, command: str = None, exit_code: int = None):
        self.command = command
        self.exit_code = exit_code
        super().__init__(message, error_code=5001, component="FFmpeg")