#!/usr/bin/env python3
# project_root/simple_encrypt.py - 独立加密脚本

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
import json


class SimpleEncryptor:
    """简易加密器"""
    
    def __init__(self):
        """初始化加密器"""
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
    
    def encrypt_video(self, input_path: str, output_path: str, 
                     password: str, notice_duration: int = 10) -> bool:
        """
        加密视频文件
        
        Args:
            input_path: 输入视频路径
            output_path: 输出加密文件路径
            password: 加密密码
            notice_duration: 提示段时长（秒）
            
        Returns:
            是否成功
        """
        try:
            print(f"正在加密: {input_path}")
            print(f"输出到: {output_path}")
            
            # 1. 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix="encrypt_")
            
            # 2. 生成提示视频
            notice_path = os.path.join(temp_dir, "notice.mp4")
            self._create_notice_video(notice_path, notice_duration)
            
            # 3. 提取视频流
            video_stream_path = os.path.join(temp_dir, "video.h264")
            self._extract_video_stream(input_path, video_stream_path)
            
            # 4. 加密视频流
            encrypted_stream_path = os.path.join(temp_dir, "video.enc")
            self._encrypt_file(video_stream_path, encrypted_stream_path, password)
            
            # 5. 创建文件头
            header_data = self._create_header(len(open(notice_path, 'rb').read()))
            
            # 6. 合并文件
            with open(output_path, 'wb') as out_f:
                # 写入文件头
                out_f.write(header_data)
                
                # 写入提示视频
                with open(notice_path, 'rb') as notice_f:
                    out_f.write(notice_f.read())
                
                # 写入加密数据
                with open(encrypted_stream_path, 'rb') as enc_f:
                    out_f.write(enc_f.read())
            
            # 7. 清理临时文件
            self._cleanup_temp_dir(temp_dir)
            
            print(f"✓ 加密成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"✗ 加密失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_notice_video(self, output_path: str, duration: int):
        """创建提示视频"""
        # 创建临时文本文件
        temp_text = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_text.write("本视频为加密内容\n请使用官方播放器播放完整视频\n\n购买地址: https://example.com")
        temp_text.close()
        
        try:
            # 使用FFmpeg生成提示视频
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c=black:s=1280x720:d={duration}',
                '-vf', f"drawtext=textfile='{temp_text.name}':fontsize=30:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
                '-c:v', 'libx264',
                '-t', str(duration),
                output_path,
                '-y'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"创建提示视频失败: {result.stderr}")
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_text.name):
                os.remove(temp_text.name)
    
    def _extract_video_stream(self, input_path: str, output_path: str):
        """提取视频流"""
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'copy',
            '-an',  # 去掉音频
            '-f', 'h264',
            output_path,
            '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"提取视频流失败: {result.stderr}")
    
    def _encrypt_file(self, input_path: str, output_path: str, password: str):
        """加密文件"""
        # 生成密钥
        key = hashlib.sha256(password.encode()).digest()
        
        # 创建AES-CTR加密器
        iv = b'\x00' * 16  # 简单的IV
        counter = Counter.new(128, initial_value=int.from_bytes(iv, 'big'))
        cipher = AES.new(key, AES.MODE_CTR, counter=counter)
        
        # 加密数据
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            while True:
                chunk = f_in.read(8192)
                if not chunk:
                    break
                encrypted = cipher.encrypt(chunk)
                f_out.write(encrypted)
    
    def _create_header(self, notice_length: int) -> bytes:
        """创建文件头"""
        # 简单头格式: MAGIC(4) + VERSION(1) + NOTICE_LENGTH(4)
        magic = b'ENCV'
        version = 1
        return magic + bytes([version]) + notice_length.to_bytes(4, 'big')
    
    def _cleanup_temp_dir(self, temp_dir: str):
        """清理临时目录"""
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def encrypt_single():
    """加密单个文件"""
    parser = argparse.ArgumentParser(description='加密单个视频文件')
    parser.add_argument('input_file', help='输入视频文件')
    parser.add_argument('output_file', help='输出加密文件')
    parser.add_argument('-p', '--password', help='密码（可选，不提供则提示输入）')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input_file):
        print(f"错误: 输入文件不存在: {args.input_file}")
        return False
    
    # 获取密码
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("请输入加密密码: ")
        confirm = getpass.getpass("请再次输入密码: ")
        if password != confirm:
            print("错误: 两次输入的密码不匹配")
            return False
    
    # 执行加密
    encryptor = SimpleEncryptor()
    return encryptor.encrypt_video(args.input_file, args.output_file, password)


def encrypt_folder():
    """加密文件夹"""
    parser = argparse.ArgumentParser(description='加密文件夹中的所有视频')
    parser.add_argument('input_folder', help='输入文件夹')
    parser.add_argument('output_folder', help='输出文件夹')
    parser.add_argument('-p', '--password', help='密码')
    parser.add_argument('-r', '--recursive', action='store_true', 
                       help='递归处理子文件夹')
    parser.add_argument('--pattern', default='*.mp4', help='文件匹配模式')
    
    args = parser.parse_args()
    
    # 检查输入文件夹
    if not os.path.isdir(args.input_folder):
        print(f"错误: 输入文件夹不存在: {args.input_folder}")
        return False
    
    # 获取密码
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("请输入加密密码: ")
        confirm = getpass.getpass("请再次输入密码: ")
        if password != confirm:
            print("错误: 两次输入的密码不匹配")
            return False
    
    # 创建输出文件夹
    os.makedirs(args.output_folder, exist_ok=True)
    
    # 查找文件
    if args.recursive:
        search_pattern = os.path.join(args.input_folder, "**", args.pattern)
        video_files = glob.glob(search_pattern, recursive=True)
    else:
        search_pattern = os.path.join(args.input_folder, args.pattern)
        video_files = glob.glob(search_pattern)
    
    video_files.sort()
    
    if not video_files:
        print(f"没有找到匹配 {args.pattern} 的文件")
        return True
    
    print(f"找到 {len(video_files)} 个视频文件")
    
    # 处理每个文件
    encryptor = SimpleEncryptor()
    success_count = 0
    
    for i, video_file in enumerate(video_files, 1):
        try:
            # 创建输出路径
            rel_path = os.path.relpath(video_file, args.input_folder)
            output_file = os.path.join(args.output_folder, rel_path)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 添加.enc后缀
            path_obj = Path(output_file)
            output_file = str(path_obj.with_name(f"{path_obj.stem}.enc{path_obj.suffix}"))
            
            print(f"[{i}/{len(video_files)}] 处理: {rel_path}")
            
            # 加密
            success = encryptor.encrypt_video(video_file, output_file, password)
            
            if success:
                success_count += 1
                print(f"  ✓ 完成")
            else:
                print(f"  ✗ 失败")
                
        except Exception as e:
            print(f"  ✗ 出错: {e}")
    
    print(f"\n处理完成: {success_count}/{len(video_files)} 成功")
    return success_count > 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简易视频加密工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 单个文件加密命令
    single_parser = subparsers.add_parser('file', help='加密单个文件')
    single_parser.add_argument('input_file', help='输入视频文件')
    single_parser.add_argument('output_file', help='输出加密文件')
    single_parser.add_argument('-p', '--password', help='密码')
    
    # 文件夹加密命令
    folder_parser = subparsers.add_parser('folder', help='加密文件夹')
    folder_parser.add_argument('input_folder', help='输入文件夹')
    folder_parser.add_argument('output_folder', help='输出文件夹')
    folder_parser.add_argument('-p', '--password', help='密码')
    folder_parser.add_argument('-r', '--recursive', action='store_true', 
                              help='递归处理子文件夹')
    folder_parser.add_argument('--pattern', default='*.mp4', 
                              help='文件匹配模式')
    
    args = parser.parse_args()
    
    if not args.command:
        print("请选择一个命令:")
        print("  加密单个文件: python simple_encrypt.py file 输入.mp4 输出.enc.mp4")
        print("  加密文件夹: python simple_encrypt.py folder 输入目录 输出目录")
        return
    
    if args.command == 'file':
        success = encrypt_single()
    elif args.command == 'folder':
        success = encrypt_folder()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()