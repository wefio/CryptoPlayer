# player/config/config_manager.py
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file if config_file else "config.json"
        self.default_config = {
            "ffmpeg": {
                "ffmpeg_path": "ffmpeg",
                "ffprobe_path": "ffprobe"
            },
            "encryption": {
                "default_algorithm": "AES-CTR",
                "key_derivation": "PBKDF2",
                "salt_length": 16,
                "key_size": 32,
                "iterations": 100000
            },
            "metadata": {
                "whitelist": [
                    "title",
                    "artist",
                    "comment",
                    "description",
                    "copyright",
                    "encoder",
                    "creation_time"
                ],
                "max_field_length": 1024
            },
            "file_format": {
                "magic": b"ENCV",
                "version": 1,
                "reserved_size": 32
            },
            "player": {
                "skip_notice_by_default": False,
                "show_metadata_on_start": True,
                "platform_adaptation": True
            }
        }
        self._config = None
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置
        
        Returns:
            配置字典
            
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON解析错误
        """
        if self._config is not None:
            return self._config
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 深度合并配置
                self._config = self._deep_merge(self.default_config, user_config)
        else:
            self._config = self.default_config.copy()
            # 保存默认配置
            self.save_config(self._config)
        
        return self._config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        保存配置
        
        Args:
            config: 配置字典
            
        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def get_algorithm_config(self, algorithm_name: str) -> Dict[str, Any]:
        """
        获取算法特定配置
        
        Args:
            algorithm_name: 算法名称
            
        Returns:
            算法配置
        """
        config = self.load_config()
        encryption_config = config.get("encryption", {})
        
        algorithm_configs = {
            "AES-CTR": {
                "mode": "CTR",
                "key_size": 32,
                "iv_size": 16
            },
            "AES-CBC": {
                "mode": "CBC",
                "key_size": 32,
                "iv_size": 16
            },
            "ChaCha20": {
                "nonce_size": 12,
                "key_size": 32
            }
        }
        
        return algorithm_configs.get(algorithm_name, {})
    
    def get_ffmpeg_path(self) -> str:
        """获取FFmpeg路径"""
        config = self.load_config()
        return config.get("ffmpeg", {}).get("ffmpeg_path", "ffmpeg")
    
    def get_ffprobe_path(self) -> str:
        """获取FFprobe路径"""
        config = self.load_config()
        return config.get("ffmpeg", {}).get("ffprobe_path", "ffprobe")
    
    def get_default_algorithm(self) -> str:
        """获取默认加密算法"""
        config = self.load_config()
        return config.get("encryption", {}).get("default_algorithm", "AES-CTR")
    
    @staticmethod
    def _deep_merge(base: Dict, update: Dict) -> Dict:
        """深度合并两个字典"""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
