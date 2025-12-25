# player/core/video_processor.py
import os
import sys
from typing import Optional

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from player.config.config_manager import ConfigManager
    from player.core.encryptor import Encryptor
    from player.core.decryptor import Decryptor
    from player.metadata.metadata_handler import MetadataHandler
    from player.exceptions.custom_exceptions import VideoEncryptionError, PasswordError, CryptoError
    from player.utils.file_utils import FileUtils
except ImportError:
    # 备用导入方式
    from config.config_manager import ConfigManager
    from core.encryptor import Encryptor
    from core.decryptor import Decryptor
    from metadata.metadata_handler import MetadataHandler
    from exceptions.custom_exceptions import VideoEncryptionError, PasswordError, CryptoError
    from utils.file_utils import FileUtils



class VideoProcessor:
    """视频处理器 - 主控制器"""

    def __init__(self, config_path: str = None):
        """
        初始化视频处理器

        Args:
            config_path: 配置文件路径
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()

        # 初始化组件
        self.encryptor = None
        self.decryptor = None
        self.metadata_handler = None

        self._init_components()

    def _init_components(self):
        """初始化所有组件"""
        # 获取默认算法
        default_algorithm = self.config_manager.get_default_algorithm()

        # 初始化加密器、解密器和元数据处理器
        self.encryptor = Encryptor(default_algorithm)
        self.decryptor = Decryptor(default_algorithm)
        self.metadata_handler = MetadataHandler()

    def encrypt_video(self, input_path: str, output_path: str, password: str,
                      notice_video_path: Optional[str] = None,
                      metadata_config: Optional[str] = None,
                      pure_encrypt: bool = False) -> bool:
        """
        执行完整加密流程

        Args:
            input_path: 原始视频路径
            output_path: 输出加密文件路径
            password: 加密密码
            notice_video_path: 提示视频路径（可选）
            metadata_config: 元数据配置路径（可选）
            pure_encrypt: 是否纯加密（无提示段），为True时忽略notice_video_path

        Returns:
            成功/失败

        Raises:
            VideoEncryptionError: 加密失败
        """
        import tempfile
        temp_notice_path = None
        try:
            # 验证输入文件
            if not os.path.exists(input_path):
                raise VideoEncryptionError(f"输入文件不存在: {input_path}")

            # 纯加密模式：notice_video_path设为None
            if pure_encrypt:
                notice_video_path = None
            # 如果没有提供提示视频且不是纯加密模式，则生成默认提示视频
            elif not notice_video_path:
                temp_notice_path = self._generate_default_notice_video()
                notice_video_path = temp_notice_path

            # 确保输出目录存在
            FileUtils.ensure_directory(os.path.dirname(output_path))

            # 执行加密（notice_video_path可以为None，表示纯加密无提示段）
            success = self.encryptor.generate_encrypted_file(
                plain_video_path=input_path,
                notice_video_path=notice_video_path,
                password=password,
                output_path=output_path,
                metadata_config=metadata_config
            )

            return success

        except Exception as e:
            if isinstance(e, VideoEncryptionError):
                raise e
            else:
                raise VideoEncryptionError(f"加密视频失败: {e}")
        finally:
            # 清理临时提示视频
            if temp_notice_path and os.path.exists(temp_notice_path):
                os.remove(temp_notice_path)

    def decrypt_and_play(self, encrypted_path: str, password: str,
                         skip_notice: bool = False) -> bool:
        """
        解密并播放视频

        Args:
            encrypted_path: 加密文件路径
            password: 解密密码
            skip_notice: 是否跳过提示段

        Returns:
            成功/失败

        Raises:
            VideoEncryptionError: 解密或播放失败
        """
        try:
            # 验证加密文件
            if not os.path.exists(encrypted_path):
                raise VideoEncryptionError(f"加密文件不存在: {encrypted_path}")

            # 加载加密文件
            from ..file.encrypted_video import EncryptedVideoFile
            encrypted_file = EncryptedVideoFile(encrypted_path)

            # 播放提示段（如果不跳过）
            if not skip_notice:
                if encrypted_file.notice_data:
                    self._play_notice_section(encrypted_file)

            # 解密视频流到临时文件
            temp_video_path = self.decryptor.decrypt_to_temp_file(encrypted_path, password)

            # 播放解密后的视频
            from ..ffmpeg.ffmpeg_wrapper import FFmpegWrapper
            ffmpeg = FFmpegWrapper()

            # 设置窗口标题
            title = "加密视频播放器 - 正在播放"
            success = ffmpeg.play_video(temp_video_path, title=title)

            # 清理临时文件
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)

            return success

        except PasswordError:
            raise  # 直接传递密码错误
        except Exception as e:
            if isinstance(e, VideoEncryptionError):
                raise e
            else:
                raise VideoEncryptionError(f"解密并播放失败: {e}")

    def _generate_default_notice_video(self) -> str:
        """
        生成默认提示视频

        Returns:
            提示视频文件路径
        """
        import tempfile
        from ..ffmpeg.ffmpeg_wrapper import FFmpegWrapper

        ffmpeg = FFmpegWrapper()
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)

        # 尝试从notice_assets/notice.txt读取notice_text
        notice_text = "本视频为加密内容，请使用官方播放器播放完整视频。\n\n购买地址：https://example.com"
        
        # 检查notice_assets/notice.txt文件 - 使用更可靠的路径
        # 尝试多个可能的路径位置
        possible_paths = [
            os.path.join(current_dir, 'notice_assets', 'notice.txt'),
            os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'notice_assets', 'notice.txt'),
            os.path.join(current_dir, '..', 'notice_assets', 'notice.txt'),
            'notice_assets/notice.txt',
            './notice_assets/notice.txt'
        ]
        
        metadata_path = None
        for path in possible_paths:
            if os.path.exists(path):
                metadata_path = path
                break
        
        if metadata_path:
            print(f"  正在读取元数据配置: {metadata_path}")
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('notice_text='):
                            notice_text = line.split('=', 1)[1]
                            # 将\n字符转换为实际换行符
                            notice_text = notice_text.replace('\\n', '\n')
                            print(f"  ✓ 已读取提示文本")
                            break
            except Exception as e:
                print(f"  警告: 读取notice_assets/notice.txt失败: {e}")
        else:
            print(f"  警告: 未找到notice_assets/notice.txt文件，使用默认文本")

        assets = {'text': notice_text}
        success = ffmpeg.generate_notice_video(assets, temp_file.name, duration=10)

        if not success:
            raise VideoEncryptionError("生成默认提示视频失败")

        return temp_file.name

    def _play_notice_section(self, encrypted_file):
        """播放提示段"""
        from ..ffmpeg.ffmpeg_wrapper import FFmpegWrapper

        # 获取提示段的临时文件
        notice_temp_file = encrypted_file.get_notice_temp_file()
        if notice_temp_file:
            try:
                # 播放提示视频
                ffmpeg = FFmpegWrapper()
                ffmpeg.play_video(notice_temp_file, title="版权提示")
            finally:
                # 清理临时文件
                if os.path.exists(notice_temp_file):
                    os.remove(notice_temp_file)
