#!/usr/bin/env python3
# simple_encrypt_file.py - 通用文件加密工具

import os
import sys
import argparse
import getpass
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player.core.encryptor import Encryptor
from player.core.decryptor import Decryptor
from player.file.encrypted_video import EncryptedVideoFile
from player.file.file_header import FileHeader
from player.exceptions.custom_exceptions import CryptoError, FileFormatError


class FileEncryptor:
    """通用文件加密器"""
    
    SUPPORTED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv']
    
    def __init__(self, algorithm: str = "AES-CTR"):
        """
        初始化文件加密器
        
        Args:
            algorithm: 加密算法
        """
        self.algorithm = algorithm
        self.encryptor = Encryptor(algorithm)
        self.decryptor = Decryptor(algorithm)
    
    def encrypt_file(self, input_path: str, output_path: str, password: str,
                     carrier_video_path: str = None, pure_mode: bool = False) -> bool:
        """
        加密文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            password: 加密密码
            carrier_video_path: 载体视频路径（用于隐写术）
            pure_mode: 纯加密模式（无载体视频）
            
        Returns:
            是否成功
        """
        try:
            # 读取输入文件
            with open(input_path, 'rb') as f:
                file_data = f.read()
            
            print(f"输入文件: {input_path}")
            print(f"文件大小: {len(file_data)} 字节")
            
            # 加密数据
            encrypted_data, encryption_info = self.encryptor.encrypt_stream(file_data, password)
            print(f"✓ 加密完成，加密后大小: {len(encrypted_data)} 字节")
            
            # 创建文件头
            header = FileHeader()
            header.set_encryption_info(
                algorithm=encryption_info['algorithm'],
                salt=encryption_info['salt'],
                iv_nonce=encryption_info['iv_nonce']
            )
            
            # 准备提示段数据（载体视频）
            notice_data = b''
            if carrier_video_path and os.path.exists(carrier_video_path):
                with open(carrier_video_path, 'rb') as f:
                    notice_data = f.read()
                print(f"✓ 载体视频已加载: {len(notice_data)} 字节")
            
            # 创建加密文件
            encrypted_file = EncryptedVideoFile()
            encrypted_file.create_from_parts(notice_data, encrypted_data, header)
            encrypted_file.save_file(output_path)
            
            print(f"✓ 加密文件已保存: {output_path}")
            
            # 设置输出文件扩展名
            if carrier_video_path:
                # 使用载体视频的扩展名（隐写模式，输出伪装成载体视频格式）
                ext = os.path.splitext(carrier_video_path)[1]
                new_output = os.path.splitext(output_path)[0] + ext
                if new_output != output_path:
                    os.rename(output_path, new_output)
                    print(f"✓ 隐写模式：输出文件伪装为{ext}格式")
                    print(f"✓ 最终输出路径: {new_output}")
                    output_path = new_output
            
            return True
            
        except Exception as e:
            print(f"✗ 加密失败: {e}")
            return False
    
    def decrypt_file(self, input_path: str, output_path: str, password: str) -> bool:
        """
        解密文件
        
        Args:
            input_path: 加密文件路径
            output_path: 输出文件路径
            password: 解密密码
            
        Returns:
            是否成功
        """
        try:
            # 加载加密文件
            encrypted_file = EncryptedVideoFile(input_path)
            
            print(f"输入文件: {input_path}")
            print(f"提示段大小: {len(encrypted_file.notice_data)} 字节")
            print(f"加密段大小: {len(encrypted_file.encrypted_data)} 字节")
            
            # 获取加密信息
            encryption_info = encrypted_file.header.get_encryption_info()
            print(f"加密算法: {encryption_info.get('algorithm', 'N/A')}")
            
            # 解密数据
            encrypted_data = encrypted_file.extract_encrypted_section()
            decrypted_data = self.decryptor.decrypt_stream(encrypted_data, password, encryption_info)
            print(f"✓ 解密完成，解密后大小: {len(decrypted_data)} 字节")
            
            # 保存解密后的文件
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            print(f"✓ 解密文件已保存: {output_path}")
            return True
            
        except Exception as e:
            print(f"✗ 解密失败: {e}")
            return False
    
    def get_file_type(self, file_path: str) -> str:
        """
        获取文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型（video/image/text/other）
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in self.SUPPORTED_VIDEO_EXTENSIONS:
            return 'video'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return 'image'
        elif ext in ['.txt', '.csv', '.json', '.xml', '.log']:
            return 'text'
        elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            return 'archive'
        elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']:
            return 'document'
        else:
            return 'other'


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='通用文件加密工具 - 支持加密任意文件类型（zip、txt、图片等）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 纯加密模式（生成.enc.mp4文件）
  python simple_encrypt_file.py encrypt input.zip encrypted_output.enc.mp4 -p "password"
  
  # 使用载体视频（隐写术，加密文件伪装成视频）
  python simple_encrypt_file.py encrypt input.txt secret.mp4 -p "password" -c carrier.mp4
  
  # 解密文件
  python simple_encrypt_file.py decrypt secret.mp4 output.txt -p "password"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 加密命令
    encrypt_parser = subparsers.add_parser('encrypt', help='加密文件')
    encrypt_parser.add_argument('input', help='输入文件路径')
    encrypt_parser.add_argument('output', help='输出文件路径')
    encrypt_parser.add_argument('-p', '--password', help='加密密码（不提供则提示输入）')
    encrypt_parser.add_argument('-c', '--carrier', help='载体视频路径（用于隐写术，加密文件将伪装成该视频）')
    encrypt_parser.add_argument('-a', '--algorithm', default='AES-CTR',
                               choices=['AES-CTR', 'AES-CBC', 'ChaCha20'],
                               help='加密算法（默认：AES-CTR）')
    encrypt_parser.add_argument('--pure', action='store_true',
                               help='纯加密模式（不使用载体视频）')
    
    # 解密命令
    decrypt_parser = subparsers.add_parser('decrypt', help='解密文件')
    decrypt_parser.add_argument('input', help='加密文件路径')
    decrypt_parser.add_argument('output', help='输出文件路径')
    decrypt_parser.add_argument('-p', '--password', help='解密密码（不提供则提示输入）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        sys.exit(1)
    
    # 获取密码
    password = args.password
    if not password:
        password = getpass.getpass("请输入密码: ")
    
    # 创建加密器
    encryptor = FileEncryptor(args.algorithm if args.command == 'encrypt' else 'AES-CTR')
    
    # 执行命令
    if args.command == 'encrypt':
        # 检查载体视频
        carrier = args.carrier if hasattr(args, 'carrier') else None
        
        if carrier and not os.path.exists(carrier):
            print(f"错误: 载体视频不存在: {carrier}")
            sys.exit(1)
        
        # 如果指定了--pure，清除carrier
        if hasattr(args, 'pure') and args.pure:
            carrier = None
        
        # 执行加密
        success = encryptor.encrypt_file(args.input, args.output, password, carrier)
        sys.exit(0 if success else 1)
        
    elif args.command == 'decrypt':
        # 执行解密
        success = encryptor.decrypt_file(args.input, args.output, password)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
