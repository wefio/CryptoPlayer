# player/cli/progress.py
import sys
import time
from typing import Optional


class ProgressBar:
    """进度条显示"""

    def __init__(self, total: int, description: str = "", length: int = 40):
        """
        初始化进度条

        Args:
            total: 总进度
            description: 描述文字
            length: 进度条长度
        """
        self.total = total
        self.description = description
        self.length = length
        self.start_time = time.time()
        self.current = 0

    def update(self, current: int, description: Optional[str] = None):
        """
        更新进度

        Args:
            current: 当前进度
            description: 新的描述文字（可选）
        """
        self.current = current
        if description:
            self.description = description

        percentage = (current / self.total) * 100 if self.total > 0 else 0
        filled_length = int(self.length * current // self.total)
        bar = '█' * filled_length + '░' * (self.length - filled_length)

        # 计算已用时间和估计剩余时间
        elapsed_time = time.time() - self.start_time
        if current > 0:
            estimated_total = elapsed_time * self.total / current
            remaining_time = estimated_total - elapsed_time
            time_str = f"ETA: {self._format_time(remaining_time)}"
        else:
            time_str = "ETA: --:--"

        # 显示进度
        sys.stdout.write(f"\r{self.description} |{bar}| {percentage:.1f}% ({current}/{self.total}) {time_str}")
        sys.stdout.flush()

        if current >= self.total:
            sys.stdout.write("\n")

    def finish(self):
        """完成进度条"""
        self.update(self.total)
        print(f"完成！总用时: {self._format_time(time.time() - self.start_time)}")

    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"