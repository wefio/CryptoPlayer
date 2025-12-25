# player/utils/video_utils.py
import json
import subprocess
from typing import Optional, Dict, Any
from ..exceptions.custom_exceptions import FFmpegError


class VideoUtils:
    """视频相关工具类"""
    
    def __init__(self, ffprobe_path: str = "ffprobe"):
        """
        初始化视频工具
        
        Args:
            ffprobe_path: ffprobe可执行文件路径
        """
        self.ffprobe_path = ffprobe_path
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        获取视频基本信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典
            
        Raises:
            FFmpegError: ffprobe执行失败
        """
        import sys
        
        cmd = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        try:
            # Windows下使用GBK编码处理输出
            encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'
            result = subprocess.run(cmd, capture_output=True, text=True, encoding=encoding, errors='ignore', check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise FFmpegError(
                f"获取视频信息失败: {e.stderr}",
                command=" ".join(cmd),
                exit_code=e.returncode
            )
        except json.JSONDecodeError:
            raise FFmpegError("解析视频信息失败")
    
    def validate_video_file(self, video_path: str) -> tuple:
        """
        验证视频文件有效性
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            info = self.get_video_info(video_path)
            if 'streams' not in info or len(info['streams']) == 0:
                return False, "没有找到视频流"
            
            # 检查是否有视频流
            has_video = any(stream.get('codec_type') == 'video' for stream in info['streams'])
            if not has_video:
                return False, "没有找到视频轨道"
            
            return True, "文件有效"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        格式化时长
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化后的时长字符串 (HH:MM:SS)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
