# player/cli/interface.py
import getpass
from typing import Optional
from ..exceptions.custom_exceptions import PasswordError, VideoEncryptionError
from ..utils.video_utils import VideoUtils


class CLIInterface:
    """命令行接口"""

    def __init__(self, ffprobe_path: str = "ffprobe"):
        """
        初始化命令行接口

        Args:
            ffprobe_path: ffprobe路径
        """
        self.video_utils = VideoUtils(ffprobe_path)

    def prompt_for_password(self, confirm: bool = False) -> str:
        """
        提示输入密码

        Args:
            confirm: 是否需要确认密码（用于加密时）

        Returns:
            密码
        """
        password = getpass.getpass("请输入密码: ")

        if confirm:
            password_confirm = getpass.getpass("请再次输入密码: ")
            if password != password_confirm:
                raise PasswordError("两次输入的密码不匹配")

        return password

    def show_video_info(self, video_path: str):
        """
        显示视频信息

        Args:
            video_path: 视频路径
        """
        try:
            info = self.video_utils.get_video_info(video_path)
            format_info = info.get('format', {})
            streams = info.get('streams', [])

            print(f"\n视频信息:")
            print(f"  文件: {format_info.get('filename', 'N/A')}")
            print(f"  格式: {format_info.get('format_long_name', 'N/A')}")
            print(f"  时长: {format_info.get('duration', 'N/A')} 秒")
            print(f"  大小: {format_info.get('size', 'N/A')} 字节")

            for i, stream in enumerate(streams):
                codec_type = stream.get('codec_type', 'unknown')
                print(f"  流 {i}: {codec_type} - {stream.get('codec_long_name', 'N/A')}")

        except Exception as e:
            print(f"获取视频信息失败: {e}")

    def ask_skip_notice(self) -> bool:
        """
        询问是否跳过提示段

        Returns:
            是否跳过
        """
        response = input("是否跳过提示段？(y/n, 默认n): ").strip().lower()
        return response == 'y' or response == 'yes'

    def show_progress(self, current: int, total: int, message: str = ""):
        """
        显示进度条

        Args:
            current: 当前进度
            total: 总进度
            message: 进度信息
        """
        if total == 0:
            return

        percentage = (current / total) * 100
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        if message:
            print(f"\r{message} |{bar}| {percentage:.1f}% ({current}/{total})", end='')
        else:
            print(f"\r|{bar}| {percentage:.1f}% ({current}/{total})", end='')

        if current >= total:
            print()  # 换行

    def show_error(self, error: Exception):
        """显示错误信息"""
        if isinstance(error, PasswordError):
            print(f"密码错误: {error.error_message}")
            if error.remaining_attempts > 0:
                print(f"剩余尝试次数: {error.remaining_attempts}")
        elif isinstance(error, VideoEncryptionError):
            print(f"视频处理错误: {error.error_message}")
            if error.component:
                print(f"错误组件: {error.component}")
        else:
            print(f"发生错误: {error}")

    def show_success(self, message: str):
        """显示成功信息"""
        print(f"✓ {message}")