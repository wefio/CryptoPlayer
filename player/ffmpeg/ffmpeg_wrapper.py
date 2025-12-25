# player/ffmpeg/ffmpeg_wrapper.py
import subprocess
import os
import tempfile
from typing import Dict, Optional, List
from ..exceptions.custom_exceptions import FFmpegError


class FFmpegWrapper:
    """FFmpeg封装器"""
    
    def __init__(self, ffmpeg_path: str = None, ffprobe_path: str = None):
        """
        初始化FFmpeg封装器
        
        Args:
            ffmpeg_path: ffmpeg可执行文件路径（None表示自动检测）
            ffprobe_path: ffprobe可执行文件路径（None表示自动检测）
        """
        # 自动检测FFmpeg路径
        self.ffmpeg_path = self._detect_ffmpeg_path(ffmpeg_path, 'ffmpeg', 'ffmpeg.exe')
        self.ffprobe_path = self._detect_ffmpeg_path(ffprobe_path, 'ffprobe', 'ffprobe.exe')
        
        # 验证FFmpeg是否可用
        self._verify_ffmpeg()
    
    def _detect_ffmpeg_path(self, provided_path: str = None, 
                           binary_name: str = "ffmpeg", 
                           windows_binary: str = "ffmpeg.exe") -> str:
        """
        自动检测FFmpeg可执行文件路径
        
        优先级：
        1. 用户提供的路径
        2. 内置FFmpeg（player/ffmpeg/bin/）
        3. 系统PATH中的命令
        
        Args:
            provided_path: 用户提供的路径
            binary_name: Linux/macOS二进制名称
            windows_binary: Windows可执行文件名
            
        Returns:
            检测到的FFmpeg路径
        """
        import sys
        
        # 1. 如果用户提供了路径，优先使用
        if provided_path:
            return provided_path
        
        # 2. 检查内置FFmpeg（仅Windows）
        if sys.platform == 'win32':
            # 获取player/ffmpeg/bin/目录的绝对路径
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            builtin_ffmpeg_dir = os.path.join(current_dir, 'ffmpeg', 'bin')
            builtin_ffmpeg = os.path.join(builtin_ffmpeg_dir, windows_binary)
            
            if os.path.exists(builtin_ffmpeg):
                print(f"  ✓ 使用内置FFmpeg: {builtin_ffmpeg}")
                return builtin_ffmpeg
            else:
                print(f"  未找到内置FFmpeg: {builtin_ffmpeg}")
        
        # 3. 使用系统PATH中的命令
        return binary_name
    
    def _verify_ffmpeg(self):
        """验证FFmpeg是否可用"""
        try:
            subprocess.run([self.ffmpeg_path, '-version'], 
                          capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise FFmpegError(f"FFmpeg不可用，请确保 {self.ffmpeg_path} 在PATH中")
    
    def extract_video_stream(self, input_path: str, output_path: str, 
                            codec: str = "copy") -> bool:
        """
        提取视频裸流（包含音频）
        
        Args:
            input_path: 输入视频路径
            output_path: 输出裸流路径
            codec: 编码器（copy表示复制，不重新编码）
            
        Returns:
            是否成功
            
        Raises:
            FFmpegError: FFmpeg执行失败
        """
        import sys
        
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-c:v', codec,
            '-c:a', 'copy',  # 保留音频
            '-f', 'mp4',  # 使用MP4容器格式以支持视频和音频
            output_path,
            '-y'  # 覆盖输出文件
        ]
        
        try:
            # Windows下使用GBK编码处理输出
            encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'
            result = subprocess.run(cmd, capture_output=True, text=True, encoding=encoding, errors='ignore', check=True)
            return True
        except subprocess.CalledProcessError as e:
            raise FFmpegError(
                f"提取视频流失败: {e.stderr}",
                command=" ".join(cmd),
                exit_code=e.returncode
            )
    
    def generate_notice_video(self, assets: Dict, output_path: str, 
                             duration: int = 10) -> bool:
        """
        生成提示视频
        
        Args:
            assets: 素材字典 {type: path} 或 {text: "文本内容"}
            output_path: 输出路径
            duration: 视频时长（秒）
            
        Returns:
            是否成功
        """
        import sys
        
        # 检查是否是视频文件路径
        if 'path' in assets and assets['path']:
            # 直接使用提供的视频文件
            video_path = assets['path']
            if os.path.exists(video_path):
                try:
                    # 复制视频到输出路径
                    cmd = [
                        self.ffmpeg_path,
                        '-i', video_path,
                        '-c', 'copy',
                        output_path,
                        '-y'
                    ]
                    # Windows下使用GBK编码处理输出
                    encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'
                    subprocess.run(cmd, capture_output=True, text=True, encoding=encoding, errors='ignore', check=True)
                    return True
                except Exception as e:
                    raise FFmpegError(f"使用提示视频失败: {str(e)}")
        
        # 否则生成文本视频
        notice_text = assets.get('text', '请使用官方播放器播放完整内容')
        
        # 将\n替换为实际的换行符
        notice_text = notice_text.replace('\\n', '\n')
        
        # 计算多行文本的位置和布局
        lines = notice_text.split('\n')
        
        try:
            # 视频参数
            width = 1280
            height = 720
            font_size = 36
            line_height = font_size + 20
            total_text_height = len(lines) * line_height
            start_y = (height - total_text_height) // 2 + font_size
            
            # 构建多行文本绘制命令
            drawtext_filters = []
            for i, line in enumerate(lines):
                if line.strip():  # 只绘制非空行
                    # 转义文本中的特殊字符
                    escaped_line = line.replace('\\', '\\\\').replace(':', '\\:').replace("'", "'\\\\''")
                    y_pos = start_y + i * line_height
                    
                    # 添加阴影和边框效果
                    filter_text = (
                        f"drawtext="
                        f"font='sans-serif':"
                        f"fontsize={font_size}:"
                        f"fontcolor=white:"
                        f"x=(w-text_w)/2:"
                        f"y={y_pos}:"
                        f"box=1:"
                        f"boxcolor=black@0.7:"
                        f"boxborderw=5:"
                        f"shadowx=2:"
                        f"shadowy=2:"
                        f"shadowcolor=black@0.5:"
                        f"text='{escaped_line}'"
                    )
                    drawtext_filters.append(filter_text)
            
            # 组合所有文本滤镜
            vf = ','.join(drawtext_filters) if drawtext_filters else None
            
            cmd = [
                self.ffmpeg_path,
                '-f', 'lavfi',
                '-i', f'color=c=black:s={width}x{height}:d={duration}',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-t', str(duration),
            ]
            
            if vf:
                cmd.extend(['-vf', vf])
            
            cmd.extend([output_path, '-y'])
            
            # Windows下使用GBK编码处理输出
            encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'
            result = subprocess.run(cmd, capture_output=True, text=True, encoding=encoding, errors='ignore', check=False)
            
            # 检查执行结果
            if result.returncode != 0:
                raise FFmpegError(f"生成提示视频失败: {result.stderr}")
                
            return True
        except Exception as e:
            raise FFmpegError(f"生成提示视频失败: {str(e)}")
    
    def play_video(self, video_path: str, title: str = None, 
                  window_size: str = None, auto_fit: bool = True) -> bool:
        """
        播放视频
        
        Args:
            video_path: 视频路径
            title: 窗口标题
            window_size: 窗口大小（如 "800x600"），如果指定则不使用自动缩放
            auto_fit: 是否自动适应屏幕（默认True）
            
        Returns:
            是否成功
        """
        import locale
        import sys
        
        cmd = [self.ffmpeg_path, '-i', video_path]
        
        if title:
            cmd.extend(['-window_title', title])
        
        # 获取屏幕尺寸（仅Windows）
        screen_width, screen_height = self._get_screen_size()
        
        # 如果启用了自动适应且未指定窗口大小
        if auto_fit and window_size is None and screen_width > 0 and screen_height > 0:
            # 获取视频信息
            try:
                video_info = self.get_video_info(video_path)
                video_width = video_info.get('streams', [{}])[0].get('width', 0)
                video_height = video_info.get('streams', [{}])[0].get('height', 0)
                
                # 如果视频尺寸超过屏幕，则缩放
                if video_width > screen_width or video_height > screen_height:
                    # 计算缩放比例，保持宽高比
                    scale_x = screen_width / video_width
                    scale_y = screen_height / video_height
                    scale = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
                    
                    new_width = int(video_width * scale)
                    new_height = int(video_height * scale)
                    window_size = f"{new_width}x{new_height}"
                    print(f"  视频分辨率 {video_width}x{video_height} 超出屏幕，自动缩放至 {window_size}")
            except Exception as e:
                print(f"  警告: 无法获取视频信息: {e}")
        
        if window_size:
            cmd.extend(['-x', window_size.split('x')[0], '-y', window_size.split('x')[1]])
        
        # 使用ffplay播放（假设ffplay可用）
        cmd[0] = cmd[0].replace('ffmpeg', 'ffplay')
        
        try:
            # Windows下使用GBK编码处理输出
            encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'
            result = subprocess.run(cmd, capture_output=True, text=True, encoding=encoding, errors='ignore')
            return result.returncode == 0
        except Exception as e:
            print(f"播放视频失败: {e}")
            return False
    
    def _get_screen_size(self) -> tuple:
        """
        获取屏幕分辨率
        
        Returns:
            (width, height) 或 (0, 0) 如果无法获取
        """
        try:
            import ctypes
            user32 = ctypes.windll.user32
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        except Exception:
            return 0, 0
    
    def add_metadata(self, input_path: str, output_path: str, 
                    metadata: Dict[str, str]) -> bool:
        """
        为视频添加元数据
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            metadata: 元数据字典
            
        Returns:
            是否成功
        """
        import sys
        
        # 如果输出路径与输入路径相同，使用临时文件
        use_temp = output_path == input_path
        temp_output = None
        
        if use_temp:
            import tempfile
            temp_output = tempfile.mktemp(suffix='.mp4')
            final_output = temp_output
        else:
            final_output = output_path
        
        cmd = [self.ffmpeg_path, '-i', input_path]
        
        # 添加元数据参数
        for key, value in metadata.items():
            cmd.extend(['-metadata', f'{key}={value}'])
        
        cmd.extend(['-c', 'copy', final_output, '-y'])
        
        try:
            # Windows下使用GBK编码处理输出
            encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'
            subprocess.run(cmd, capture_output=True, text=True, encoding=encoding, errors='ignore', check=True)
            
            # 如果使用了临时文件，替换原文件
            if use_temp and temp_output:
                import shutil
                shutil.move(temp_output, input_path)
                if os.path.exists(temp_output):
                    os.unlink(temp_output)
            
            return True
        except subprocess.CalledProcessError as e:
            # 清理临时文件
            if temp_output and os.path.exists(temp_output):
                os.unlink(temp_output)
            raise FFmpegError(f"添加元数据失败: {e.stderr}")
    
    def concat_files(self, file_list: List[str], output_path: str) -> bool:
        """
        拼接多个文件
        
        Args:
            file_list: 文件列表
            output_path: 输出路径
            
        Returns:
            是否成功
        """
        import sys
        
        # 创建临时文件列表
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for file_path in file_list:
                f.write(f"file '{file_path}'\n")
            list_file = f.name
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c', 'copy',
                output_path,
                '-y'
            ]
            
            # Windows下使用GBK编码处理输出
            encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'
            subprocess.run(cmd, capture_output=True, text=True, encoding=encoding, errors='ignore', check=True)
            return True
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"拼接文件失败: {e.stderr}")
        finally:
            if os.path.exists(list_file):
                os.unlink(list_file)
    
    def get_video_info(self, video_path: str) -> Dict:
        """
        获取视频信息
        
        Args:
            video_path: 视频路径
            
        Returns:
            视频信息字典
        """
        import json
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
            # Windows下使用正确的编码
            encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'
            result = subprocess.run(cmd, capture_output=True, text=True, encoding=encoding, errors='ignore', check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"获取视频信息失败: {e.stderr}")
        except json.JSONDecodeError as e:
            raise FFmpegError(f"解析视频信息失败: {e}")
