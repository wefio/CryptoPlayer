#!/usr/bin/env python3
# mcp_server.py - MCP服务器，让AI调用视频加密播放器功能

import os
import sys
import json
from typing import Optional
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player.core.video_processor import VideoProcessor
from player.core.encryptor import Encryptor
from player.core.decryptor import Decryptor
from player.file.encrypted_video import EncryptedVideoFile
from player.exceptions.custom_exceptions import CryptoError, FileFormatError


class ShellVideoPlayerMCP:
    """视频加密播放器MCP服务器"""
    
    def __init__(self):
        """初始化MCP服务器"""
        self.processor = VideoProcessor()
        self.config = {
            "name": "shell-video-player",
            "version": "1.0.0",
            "description": "视频加密播放器 - 支持视频和任意文件类型的加密、解密、播放功能",
            "tools": []
        }
        self._register_tools()
    
    def _register_tools(self):
        """注册所有可用工具"""
        self.config["tools"] = [
            {
                "name": "encrypt_file",
                "description": "加密文件（支持视频和任意文件类型）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_path": {
                            "type": "string",
                            "description": "输入文件路径"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径"
                        },
                        "password": {
                            "type": "string",
                            "description": "加密密码"
                        },
                        "notice_video_path": {
                            "type": "string",
                            "description": "提示视频路径（可选，用于隐写术）"
                        },
                        "algorithm": {
                            "type": "string",
                            "enum": ["AES-CTR", "AES-CBC", "ChaCha20"],
                            "description": "加密算法（默认：AES-CTR）"
                        },
                        "pure_encrypt": {
                            "type": "boolean",
                            "description": "纯加密模式（无提示段，默认：false）"
                        }
                    },
                    "required": ["input_path", "output_path", "password"]
                }
            },
            {
                "name": "decrypt_file",
                "description": "解密加密文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_path": {
                            "type": "string",
                            "description": "加密文件路径"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径"
                        },
                        "password": {
                            "type": "string",
                            "description": "解密密码"
                        },
                        "save_notice": {
                            "type": "boolean",
                            "description": "保存提示段（载体视频，默认：false）"
                        }
                    },
                    "required": ["input_path", "output_path", "password"]
                }
            },
            {
                "name": "play_encrypted_video",
                "description": "播放加密视频",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "encrypted_path": {
                            "type": "string",
                            "description": "加密视频文件路径"
                        },
                        "password": {
                            "type": "string",
                            "description": "解密密码"
                        },
                        "skip_notice": {
                            "type": "boolean",
                            "description": "跳过提示段（默认：false）"
                        }
                    },
                    "required": ["encrypted_path", "password"]
                }
            },
            {
                "name": "get_file_info",
                "description": "获取加密文件信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "加密文件路径"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "batch_encrypt",
                "description": "批量加密文件夹中的文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_folder": {
                            "type": "string",
                            "description": "输入文件夹路径"
                        },
                        "output_folder": {
                            "type": "string",
                            "description": "输出文件夹路径"
                        },
                        "password": {
                            "type": "string",
                            "description": "加密密码"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "文件匹配模式（默认：*.mp4）"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "递归处理子文件夹（默认：false）"
                        },
                        "pure_encrypt": {
                            "type": "boolean",
                            "description": "纯加密模式（无提示段，默认：false）"
                        }
                    },
                    "required": ["input_folder", "output_folder", "password"]
                }
            },
            {
                "name": "batch_decrypt",
                "description": "批量解密文件夹中的文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_folder": {
                            "type": "string",
                            "description": "加密文件文件夹路径"
                        },
                        "output_folder": {
                            "type": "string",
                            "description": "解密文件输出文件夹路径"
                        },
                        "password": {
                            "type": "string",
                            "description": "解密密码"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "文件匹配模式（默认：*.enc.mp4）"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "递归处理子文件夹（默认：false）"
                        },
                        "save_notice": {
                            "type": "boolean",
                            "description": "保存提示段（载体视频，默认：false）"
                        }
                    },
                    "required": ["input_folder", "output_folder", "password"]
                }
            },
            {
                "name": "list_available_files",
                "description": "列出可用文件（加密/解密/输入/输出）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "folder": {
                            "type": "string",
                            "enum": ["input_plain", "encrypted_output", "decrypted_output", "all"],
                            "description": "文件夹类型"
                        }
                    }
                }
            }
        ]
    
    def get_server_info(self) -> dict:
        """获取服务器信息"""
        return self.config
    
    def encrypt_file(self, input_path: str, output_path: str, password: str,
                    notice_video_path: Optional[str] = None,
                    algorithm: str = "AES-CTR",
                    pure_encrypt: bool = False) -> dict:
        """
        加密文件
        
        Returns:
            操作结果字典
        """
        try:
            # 验证输入文件
            if not os.path.exists(input_path):
                return {
                    "success": False,
                    "error": f"输入文件不存在: {input_path}"
                }
            
            # 设置加密算法
            from player.core.crypto_factory import CryptoAlgorithmFactory
            factory = CryptoAlgorithmFactory()
            self.processor.encryptor.crypto_algorithm = factory.create_algorithm(algorithm)
            self.processor.encryptor.algorithm = algorithm
            
            # 执行加密
            success = self.processor.encrypt_video(
                input_path=input_path,
                output_path=output_path,
                password=password,
                notice_video_path=notice_video_path,
                pure_encrypt=pure_encrypt
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"文件加密成功: {output_path}",
                    "input_path": input_path,
                    "output_path": output_path,
                    "algorithm": algorithm,
                    "pure_encrypt": pure_encrypt
                }
            else:
                return {
                    "success": False,
                    "error": "加密失败"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"加密失败: {str(e)}"
            }
    
    def decrypt_file(self, input_path: str, output_path: str, password: str,
                    save_notice: bool = False) -> dict:
        """
        解密文件
        
        Returns:
            操作结果字典
        """
        try:
            # 验证输入文件
            if not os.path.exists(input_path):
                return {
                    "success": False,
                    "error": f"输入文件不存在: {input_path}"
                }
            
            # 加载加密文件
            encrypted_file = EncryptedVideoFile(input_path)
            
            # 获取加密信息
            encryption_info = encrypted_file.header.get_encryption_info()
            
            # 解密数据
            decryptor = Decryptor()
            encrypted_data = encrypted_file.extract_encrypted_section()
            decrypted_data = decryptor.decrypt_stream(encrypted_data, password, encryption_info)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 保存解密后的文件
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            result = {
                "success": True,
                "message": f"文件解密成功: {output_path}",
                "input_path": input_path,
                "output_path": output_path,
                "algorithm": encryption_info.get('algorithm', 'N/A')
            }
            
            # 保存提示段（载体视频）
            if save_notice and len(encrypted_file.notice_data) > 0:
                notice_output = os.path.splitext(output_path)[0] + "_notice.mp4"
                with open(notice_output, 'wb') as f:
                    f.write(encrypted_file.notice_data)
                result["notice_path"] = notice_output
                result["message"] += f"\n提示段已保存: {notice_output}"
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"解密失败: {str(e)}"
            }
    
    def play_encrypted_video(self, encrypted_path: str, password: str,
                            skip_notice: bool = False) -> dict:
        """
        播放加密视频
        
        Returns:
            操作结果字典
        """
        try:
            # 验证输入文件
            if not os.path.exists(encrypted_path):
                return {
                    "success": False,
                    "error": f"加密文件不存在: {encrypted_path}"
                }
            
            # 执行解密播放
            success = self.processor.decrypt_and_play(
                encrypted_path=encrypted_path,
                password=password,
                skip_notice=skip_notice
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"视频播放完成: {encrypted_path}",
                    "file_path": encrypted_path
                }
            else:
                return {
                    "success": False,
                    "error": "播放失败"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"播放失败: {str(e)}"
            }
    
    def get_file_info(self, file_path: str) -> dict:
        """
        获取加密文件信息
        
        Returns:
            文件信息字典
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"文件不存在: {file_path}"
                }
            
            # 加载加密文件
            encrypted_file = EncryptedVideoFile(file_path)
            
            # 获取加密信息
            encryption_info = encrypted_file.header.get_encryption_info()
            
            return {
                "success": True,
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "notice_size": len(encrypted_file.notice_data),
                "encrypted_size": len(encrypted_file.encrypted_data),
                "algorithm": encryption_info.get('algorithm', 'N/A'),
                "has_notice": len(encrypted_file.notice_data) > 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"获取文件信息失败: {str(e)}"
            }
    
    def batch_encrypt(self, input_folder: str, output_folder: str, password: str,
                     pattern: str = "*.mp4", recursive: bool = False,
                     pure_encrypt: bool = False) -> dict:
        """
        批量加密
        
        Returns:
            操作结果字典
        """
        import glob
        
        try:
            # 验证输入文件夹
            if not os.path.isdir(input_folder):
                return {
                    "success": False,
                    "error": f"输入文件夹不存在: {input_folder}"
                }
            
            # 查找文件
            if recursive:
                search_pattern = os.path.join(input_folder, "**", pattern)
            else:
                search_pattern = os.path.join(input_folder, pattern)
            
            files = glob.glob(search_pattern, recursive=recursive)
            
            if not files:
                return {
                    "success": False,
                    "error": f"未找到匹配的文件: {search_pattern}"
                }
            
            # 确保输出文件夹存在
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            # 批量加密
            success_count = 0
            failed_count = 0
            results = []
            
            for file_path in files:
                filename = os.path.basename(file_path)
                output_path = os.path.join(output_folder, os.path.splitext(filename)[0] + ".enc.mp4")
                
                result = self.encrypt_file(file_path, output_path, password, pure_encrypt=pure_encrypt)
                results.append({
                    "file": filename,
                    "success": result["success"],
                    "error": result.get("error")
                })
                
                if result["success"]:
                    success_count += 1
                else:
                    failed_count += 1
            
            return {
                "success": True,
                "message": f"批量加密完成: {success_count}成功, {failed_count}失败",
                "total_files": len(files),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"批量加密失败: {str(e)}"
            }
    
    def batch_decrypt(self, input_folder: str, output_folder: str, password: str,
                     pattern: str = "*.enc.mp4", recursive: bool = False,
                     save_notice: bool = False) -> dict:
        """
        批量解密
        
        Returns:
            操作结果字典
        """
        import glob
        
        try:
            # 验证输入文件夹
            if not os.path.isdir(input_folder):
                return {
                    "success": False,
                    "error": f"输入文件夹不存在: {input_folder}"
                }
            
            # 查找文件
            if recursive:
                search_pattern = os.path.join(input_folder, "**", pattern)
            else:
                search_pattern = os.path.join(input_folder, pattern)
            
            files = glob.glob(search_pattern, recursive=recursive)
            
            if not files:
                return {
                    "success": False,
                    "error": f"未找到匹配的文件: {search_pattern}"
                }
            
            # 确保输出文件夹存在
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            # 批量解密
            success_count = 0
            failed_count = 0
            results = []
            
            for file_path in files:
                filename = os.path.basename(file_path)
                output_path = os.path.join(output_folder, os.path.splitext(filename)[0] + ".mp4")
                
                result = self.decrypt_file(file_path, output_path, password, save_notice)
                results.append({
                    "file": filename,
                    "success": result["success"],
                    "error": result.get("error")
                })
                
                if result["success"]:
                    success_count += 1
                else:
                    failed_count += 1
            
            return {
                "success": True,
                "message": f"批量解密完成: {success_count}成功, {failed_count}失败",
                "total_files": len(files),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"批量解密失败: {str(e)}"
            }
    
    def list_available_files(self, folder: str = "all") -> dict:
        """
        列出可用文件
        
        Returns:
            文件列表字典
        """
        try:
            folders = []
            
            if folder == "all":
                folders = ["input_plain", "encrypted_output", "decrypted_output"]
            else:
                folders = [folder]
            
            result = {
                "success": True,
                "files": {}
            }
            
            for folder_name in folders:
                if not os.path.exists(folder_name):
                    result["files"][folder_name] = []
                    continue
                
                files = []
                for file in os.listdir(folder_name):
                    if not file.startswith('.'):
                        file_path = os.path.join(folder_name, file)
                        if os.path.isfile(file_path):
                            files.append({
                                "name": file,
                                "path": file_path,
                                "size": os.path.getsize(file_path)
                            })
                
                result["files"][folder_name] = files
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"列出文件失败: {str(e)}"
            }


def main():
    """主函数 - 用于测试MCP服务器"""
    mcp = ShellVideoPlayerMCP()
    
    # 打印服务器信息
    print("=" * 60)
    print("Shell Video Player MCP Server")
    print("=" * 60)
    print(json.dumps(mcp.get_server_info(), indent=2))
    print("\n" + "=" * 60)
    print("Available Tools:")
    print("=" * 60)
    for tool in mcp.config["tools"]:
        print(f"- {tool['name']}: {tool['description']}")
    print("\n使用方法:")
    print("1. 安装MCP客户端")
    print("2. 配置MCP服务器连接")
    print("3. 使用AI调用上述工具")


if __name__ == "__main__":
    main()
