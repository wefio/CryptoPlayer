# player/player/platform_adapter.py
import platform
import subprocess
from typing import Dict, Optional


class PlatformAdapter:
    """平台适配器"""

    def __init__(self):
        """初始化平台适配器"""
        self.system = platform.system()
        self.release = platform.release()

    def set_window_title(self, title: str) -> bool:
        """
        设置窗口标题

        Args:
            title: 窗口标题

        Returns:
            是否成功
        """
        try:
            if self.system == "Windows":
                # Windows设置标题
                import ctypes
                ctypes.windll.kernel32.SetConsoleTitleW(title)
                return True
            elif self.system == "Linux":
                # Linux设置标题
                print(f"\033]0;{title}\007", end='', flush=True)
                return True
            elif self.system == "Darwin":
                # macOS设置标题
                print(f"\033]0;{title}\007", end='', flush=True)
                return True
            else:
                return False
        except Exception:
            return False

    def set_process_info(self, info: Dict) -> bool:
        """
        设置进程信息

        Args:
            info: 进程信息

        Returns:
            是否成功
        """
        # 这个功能在不同平台上实现差异很大
        # 这里只做简单的演示
        try:
            if self.system == "Windows":
                # Windows下可以设置进程描述
                pass
            elif self.system == "Linux":
                # Linux下可以设置PR_SET_NAME
                import ctypes
                import ctypes.util
                libc = ctypes.CDLL(ctypes.util.find_library('c'))
                if hasattr(libc, 'prctl'):
                    PR_SET_NAME = 15
                    name = info.get('title', 'encrypted_player')[:16]
                    libc.prctl(PR_SET_NAME, name.encode('utf-8'), 0, 0, 0)
            return True
        except Exception:
            return False

    def get_platform_specific_ffmpeg_args(self) -> list:
        """
        获取平台特定的FFmpeg参数

        Returns:
            平台相关的FFmpeg参数列表
        """
        if self.system == "Windows":
            return ["-noborder", "-alwaysontop"]
        elif self.system == "Linux":
            return ["-noborder", "-alwaysontop"]
        elif self.system == "Darwin":
            return ["-noborder"]
        else:
            return []