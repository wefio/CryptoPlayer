#!/usr/bin/env python3
# project_root/simple_decrypt.py - 独立解密播放脚本

import os
import sys
import argparse
import getpass
import subprocess
import tempfile
import glob
from pathlib import Path
from typing import Optional, List, Dict, Any
import hashlib
from Crypto.Cipher import AES
from Crypto.Util import Counter


class SimpleDecryptor:
    """简易解密播放器"""
    
    def __init__(self):
        """初始化解密器"""
        # 检查FFmpeg是否可用
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """检查FFmpeg是否安装"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                          capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("错误: 请先安装FFmpeg并将其添加到PATH中")
            print("下载地址: https://ffmpeg.org/download.html")
            sys.exit(1)
    
    def decrypt_and_play(self, input_path: str, password: str, 
                        skip_notice: bool = False) -> bool:
        """
        解密并播放视频
        
        Args:
            input_path: 输入加密文件路径
            password: 解密密码
            skip_notice: 是否跳过提示段
            
        Returns:
            是否成功
        """
        try:
            print(f"正在播放: {input_path}")
            
            # 1. 解析加密文件
            with open(input_path, 'rb') as f:
                # 读取文件头
                header = f.read(9)  # 4+1+4=9字节
                if len(header) < 9:
                    raise Exception("文件格式错误: 文件头不完整")
                
                magic = header[:4]
                if magic != b'ENCV':
                    raise Exception("不是有效的加密视频文件")
                
                notice_length = int.from_bytes(header[5:9], 'big')
                
                # 读取提示段
                notice_data = f.read(notice_length) if not skip_notice else f.seek(notice_length)
                
                # 剩余的是加密数据
                encrypted_data = f.read()
            
            # 2. 如果不跳过提示，先播放提示
            if not skip_notice and notice_data:
                self._play_notice(notice_data)
            
            # 3. 解密视频流
            decrypted_data = self._decrypt_data(encrypted_data, password)
            
            # 4. 播放解密后的视频
            return self._play_video_stream(decrypted_data)
            
        except Exception as e:
            print(f"✗ 播放失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _play_notice(self, notice_data: bytes):
        """播放提示段"""
        # 将提示数据写入临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_file.write(notice_data)
        temp_file.close()
        
        try:
            print("播放提示段...")
            cmd = ['ffplay', '-autoexit', '-window_title', '版权提示', temp_file.name]
            subprocess.run(cmd, capture_output=True)
        finally:
            # 清理临时文件
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
    
    def _decrypt_data(self, encrypted_data: bytes, password: str) -> bytes:
        """解密数据"""
        # 生成密钥（与加密时相同）
        key = hashlib.sha256(password.encode()).digest()
        
        # 创建AES-CTR解密器
        iv = b'\x00' * 16  # 简单的IV
        counter = Counter.new(128, initial_value=int.from_bytes(iv, 'big'))
        cipher = AES.new(key, AES.MODE_CTR, counter=counter)
        
        # 解密数据
        return cipher.decrypt(encrypted_data)
    
    def _play_video_stream(self, video_data: bytes) -> bool:
        """播放视频流"""
        # 将视频数据写入临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.h264', delete=False)
        temp_file.write(video_data)
        temp_file.close()
        
        try:
            print("播放视频...")
            # 使用ffplay播放
            cmd = [
                'ffplay',
                '-window_title', '加密视频播放器',
                '-autoexit',
                temp_file.name
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)


def decrypt_single():
    """解密播放单个文件"""
    parser = argparse.ArgumentParser(description='解密播放单个加密文件')
    parser.add_argument('input_file', help='输入加密文件')
    parser.add_argument('-p', '--password', help='密码（可选）')
    parser.add_argument('-s', '--skip-notice', action='store_true', 
                       help='跳过提示段')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input_file):
        print(f"错误: 输入文件不存在: {args.input_file}")
        return False
    
    # 获取密码
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("请输入解密密码: ")
    
    # 执行解密播放
    decryptor = SimpleDecryptor()
    return decryptor.decrypt_and_play(args.input_file, password, args.skip_notice)


def decrypt_folder():
    """解密播放文件夹"""
    parser = argparse.ArgumentParser(description='解密播放文件夹中的所有加密视频')
    parser.add_argument('input_folder', help='输入文件夹')
    parser.add_argument('-p', '--password', help='密码（可选）')
    parser.add_argument('-r', '--recursive', action='store_true', 
                       help='递归处理子文件夹')
    parser.add_argument('-s', '--skip-notice', action='store_true', 
                       help='跳过所有提示段')
    parser.add_argument('--playlist', action='store_true', 
                       help='播放列表模式（连续播放）')
    parser.add_argument('--shuffle', action='store_true', 
                       help='随机播放')
    parser.add_argument('--pattern', default='*.enc.mp4', 
                       help='文件匹配模式')
    
    args = parser.parse_args()
    
    # 检查输入文件夹
    if not os.path.isdir(args.input_folder):
        print(f"错误: 输入文件夹不存在: {args.input_folder}")
        return False
    
    # 获取密码
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("请输入解密密码: ")
    
    # 查找文件
    if args.recursive:
        search_pattern = os.path.join(args.input_folder, "**", args.pattern)
        video_files = glob.glob(search_pattern, recursive=True)
    else:
        search_pattern = os.path.join(args.input_folder, args.pattern)
        video_files = glob.glob(search_pattern)
    
    video_files.sort()
    
    if not video_files:
        print(f"没有找到匹配 {args.pattern} 的加密文件")
        return True
    
    # 随机播放
    if args.shuffle:
        import random
        random.shuffle(video_files)
    
    print(f"找到 {len(video_files)} 个加密视频文件")
    
    # 处理每个文件
    decryptor = SimpleDecryptor()
    success_count = 0
    
    for i, video_file in enumerate(video_files, 1):
        try:
            rel_path = os.path.relpath(video_file, args.input_folder)
            print(f"[{i}/{len(video_files)}] 播放: {rel_path}")
            
            # 解密播放
            success = decryptor.decrypt_and_play(
                video_file, 
                password, 
                args.skip_notice
            )
            
            if success:
                success_count += 1
                print(f"  ✓ 播放完成")
            else:
                print(f"  ✗ 播放失败")
                
            # 如果不是播放列表模式，询问是否继续
            if not args.playlist and i < len(video_files):
                response = input("播放下一个文件？(y/n, 默认y): ").strip().lower()
                if response == 'n' or response == 'no':
                    print(f"已播放 {i} 个文件")
                    break
                    
        except Exception as e:
            print(f"  ✗ 出错: {e}")
            # 询问是否继续
            response = input("出错，是否继续？(y/n, 默认y): ").strip().lower()
            if response == 'n' or response == 'no':
                break
    
    print(f"\n处理完成: {success_count}/{min(i, len(video_files))} 成功")
    return success_count > 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简易视频解密播放工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 单个文件解密命令
    single_parser = subparsers.add_parser('file', help='解密播放单个文件')
    single_parser.add_argument('input_file', help='输入加密文件')
    single_parser.add_argument('-p', '--password', help='密码')
    single_parser.add_argument('-s', '--skip-notice', action='store_true', 
                              help='跳过提示段')
    
    # 文件夹解密命令
    folder_parser = subparsers.add_parser('folder', help='解密播放文件夹')
    folder_parser.add_argument('input_folder', help='输入文件夹')
    folder_parser.add_argument('-p', '--password', help='密码')
    folder_parser.add_argument('-r', '--recursive', action='store_true', 
                              help='递归处理')
    folder_parser.add_argument('-s', '--skip-notice', action='store_true', 
                              help='跳过提示段')
    folder_parser.add_argument('--playlist', action='store_true', 
                              help='播放列表模式')
    folder_parser.add_argument('--shuffle', action='store_true', 
                              help='随机播放')
    folder_parser.add_argument('--pattern', default='*.enc.mp4', 
                              help='文件匹配模式')
    
    args = parser.parse_args()
    
    if not args.command:
        print("请选择一个命令:")
        print("  播放单个文件: python simple_decrypt.py file 加密视频.enc.mp4")
        print("  播放文件夹: python simple_decrypt.py folder 加密视频目录")
        return
    
    if args.command == 'file':
        success = decrypt_single()
    elif args.command == 'folder':
        success = decrypt_folder()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()