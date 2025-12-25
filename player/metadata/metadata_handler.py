# player/metadata/metadata_handler.py
import json
import re
from typing import Dict, Any, List, Tuple
from pathlib import Path
from ..exceptions.custom_exceptions import MetadataError
from ..utils.file_utils import FileUtils
from ..metadata.metadata_validator import MetadataValidator


class MetadataHandler:
    """元数据处理器"""

    def __init__(self, config_path: str = None):
        """
        初始化元数据处理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.metadata_config = {}
        self.validator = MetadataValidator()

        if config_path:
            self.parse_config_file(config_path)

    def parse_config_file(self, config_path: str) -> Dict[str, Any]:
        """
        解析metadata.txt配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            解析后的配置字典

        Raises:
            MetadataError: 配置文件解析失败
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            metadata = {}
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 支持两种格式：key=value 和 key+=value（追加模式）
                if '=' in line:
                    if '+=' in line:
                        key, value = line.split('+=', 1)
                        append = True
                    else:
                        key, value = line.split('=', 1)
                        append = False

                    key = key.strip()
                    value = value.strip()

                    # notice_text字段只用于生成提示视频，不需要验证
                    if key == 'notice_text':
                        continue

                    # 验证字段
                    is_valid, error_msg = self.validator.validate_field(key, value)
                    if not is_valid:
                        raise MetadataError(f"字段验证失败: {error_msg}", field=key)

                    # 如果是追加模式，且字段已存在，则追加
                    if append and key in metadata:
                        # 如果已存在，用换行符连接
                        metadata[key] = metadata[key] + '\n' + value
                    else:
                        metadata[key] = value

            self.metadata_config = metadata
            return metadata
        except Exception as e:
            raise MetadataError(f"解析配置文件失败: {e}")

    def inject_metadata(self, video_path: str, metadata: Dict[str, str],
                        output_path: str = None) -> bool:
        """
        将元数据注入视频文件

        Args:
            video_path: 视频文件路径
            metadata: 元数据字典
            output_path: 输出路径，如果为None则覆盖原文件

        Returns:
            是否成功

        Raises:
            MetadataError: 注入元数据失败
        """
        try:
            if output_path is None:
                output_path = video_path

            # 使用FFmpeg添加元数据
            from ..ffmpeg.ffmpeg_wrapper import FFmpegWrapper
            ffmpeg = FFmpegWrapper()

            # 过滤出白名单内的字段
            whitelist = self.validator.whitelist
            filtered_metadata = {k: v for k, v in metadata.items() if k in whitelist}

            # 调用FFmpeg添加元数据
            success = ffmpeg.add_metadata(video_path, output_path, filtered_metadata)
            if not success:
                raise MetadataError("FFmpeg添加元数据失败")

            return True
        except Exception as e:
            raise MetadataError(f"注入元数据失败: {e}")

    def generate_udta_json(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成用户数据盒子（udta）的JSON内容

        Args:
            metadata: 原始元数据

        Returns:
            结构化udta JSON
        """
        udta = {}

        # 提取结构字段（以struct.开头的字段）
        for key, value in metadata.items():
            if key.startswith('struct.'):
                struct_key = key[7:]  # 去掉'struct.'前缀
                udta[struct_key] = value

        # 添加一些默认字段
        if 'notice_duration' not in udta:
            udta['notice_duration'] = 10

        return udta

    def write_udta_json(self, udta_data: Dict[str, Any], output_path: str) -> bool:
        """
        将udta JSON写入文件

        Args:
            udta_data: udta数据
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(udta_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            raise MetadataError(f"写入udta JSON失败: {e}")
