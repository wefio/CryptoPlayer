# player/metadata/metadata_validator.py
import re
from typing import Tuple


class MetadataValidator:
    """元数据验证器"""

    def __init__(self):
        """初始化验证器"""
        self.whitelist = [
            "title",
            "artist",
            "comment",
            "description",
            "copyright",
            "encoder",
            "creation_time"
        ]

        # 字段验证规则：正则表达式或验证函数
        self.field_patterns = {
            "title": r'^.{1,200}$',
            "artist": r'^.{1,100}$',
            "comment": r'^.{0,500}$',
            "description": r'^.{0,1000}$',
            "copyright": r'^.{0,200}$',
            "encoder": r'^.{0,100}$',
            "creation_time": r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        }

    def validate_field(self, key: str, value: str) -> Tuple[bool, str]:
        """
        验证单个字段

        Args:
            key: 字段名
            value: 字段值

        Returns:
            (是否有效, 错误信息)
        """
        # 检查字段是否在白名单中
        if key not in self.whitelist and not key.startswith('struct.'):
            return False, f"字段 '{key}' 不在白名单中，请使用白名单字段或struct.前缀"

        # 检查字段长度
        if len(value) > 1024:  # 最大长度限制
            return False, f"字段 '{key}' 长度超过1024字符"

        # 如果字段有正则表达式，进行匹配
        if key in self.field_patterns:
            pattern = self.field_patterns[key]
            if not re.match(pattern, value):
                return False, f"字段 '{key}' 的格式不正确"

        return True, ""

    def sanitize_value(self, key: str, value: str) -> str:
        """
        清理字段值中的特殊字符

        Args:
            key: 字段名
            value: 字段值

        Returns:
            净化后的值
        """
        # 移除控制字符
        sanitized = re.sub(r'[\x00-\x1F\x7F]', '', value)

        # 根据字段类型进行额外的清理
        if key == 'creation_time':
            # 确保日期时间格式
            sanitized = re.sub(r'[^\d\-: ]', '', sanitized)

        return sanitized
