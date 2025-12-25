#!/usr/bin/env python3
# simple_decrypt_file.py - 通用文件解密工具

import os
import sys
import argparse
import getpass
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player.core.decryptor import Decryptor
from player.file.encrypted_video import EncryptedVideoFile
from player.file.file_header import FileHeader
from player.exceptions.custom_exceptions import CryptoError, FileFormatError


class FileDecryptor:
    """通用文件解密器"""
    
    def __init__(self, algorithm: str = "AES-CTR"):
        """
        初始化文件解密器
        
        Args:
            algorithm: 加密算法
        """
        self.algorithm = algorithm
        self.decryptor = Decryptor(algorithm)
    
    def decrypt_to_file(self, input_path: str, output_path: str, password: str,
                       save_notice: bool = False) -> tuple[bool, str]:
        """
        解密文件并保存到指定路径
        
        Args:
            input_path: 加密文件路径
            output_path: 输出文件路径
            password: 解密密码
            save_notice: 是否保存提示段（载体视频）
            
        Returns:
            (是否成功, 消息)
        """
        try:
            # 加载加密文件
            encrypted_file = EncryptedVideoFile(input_path)
            
            print(f"输入文件: {input_path}")
            print(f"提示段大小: {len(encrypted_file.notice_data)} 字节")
            print(f"加密段大小: {len(encrypted_file.encrypted_data)} 字节")
            
            # 获取加密信息
            encryption_info = encrypted_file.header.get_encryption_info()
            algorithm = encryption_info.get('algorithm', 'N/A')
            print(f"加密算法: {algorithm}")
            
            # 解密数据
            encrypted_data = encrypted_file.extract_encrypted_section()
            decrypted_data = self.decryptor.decrypt_stream(encrypted_data, password, encryption_info)
            print(f"✓ 解密完成，解密后大小: {len(decrypted_data)} 字节")
            
            # 保存解密后的文件
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            print(f"✓ 解密文件已保存: {output_path}")
            
            # 保存提示段（载体视频）
            notice_output = None
            if save_notice and len(encrypted_file.notice_data) > 0:
                notice_output = os.path.splitext(output_path)[0] + "_notice" + os.path.splitext(output_path)[1]
                if not output_path.endswith('.mp4'):
                    notice_output = os.path.splitext(output_path)[0] + "_notice.mp4"
                
                with open(notice_output, 'wb') as f:
                    f.write(encrypted_file.notice_data)
                print(f"✓ 提示段（载体视频）已保存: {notice_output}")
            
            return True, f"解密成功: {output_path}"
            
        except CryptoError as e:
            return False, f"解密失败: {e}"
        except Exception as e:
            return False, f"解密失败: {e}"
    
    def detect_original_extension(self, encrypted_file: EncryptedVideoFile) -> str:
        """
        尝试检测原始文件扩展名
        
        Args:
            encrypted_file: 加密文件对象
            
        Returns:
            文件扩展名（默认为.mp4）
        """
        # 尝试通过文件头检测
        try:
            encrypted_data = encrypted_file.extract_encrypted_section()
            
            # 检测ZIP文件
            if encrypted_data[:4] == b'PK\x03\x04':
                return '.zip'
            
            # 检测PDF文件
            if encrypted_data[:4] == b'%PDF':
                return '.pdf'
            
            # 检测PNG文件
            if encrypted_data[:8] == b'\x89PNG\r\n\x1a\n':
                return '.png'
            
            # 检测JPEG文件
            if encrypted_data[:2] == b'\xff\xd8':
                return '.jpg'
            
            # 检测RAR文件
            if encrypted_data[:4] == b'Rar!':
                return '.rar'
            
            # 检测7Z文件
            if encrypted_data[:6] == b'7z\xbc\xaf\x27\x1c':
                return '.7z'
            
        except:
            pass
        
        # 默认返回.mp4
        return '.mp4'


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='通用文件解密工具 - 支持解密任意加密文件到指定位置',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 解密加密文件
  python simple_decrypt_file.py decrypt secret.enc.mp4 output.zip -p "password"
  
  # 解密并保存提示段（载体视频）
  python simple_decrypt_file.py decrypt secret.mp4 decrypted.mp4 -p "password" --save-notice
  
  # 解密到指定目录（自动检测文件类型）
  python simple_decrypt_file.py decrypt encrypted_output/ decrypted_output/ -p "password"
  
  # 批量解密（使用batch_decrypt_save.py）
  python batch_decrypt_save.py encrypted_output/ decrypted_output/ -p "password"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 解密命令
    decrypt_parser = subparsers.add_parser('decrypt', help='解密文件')
    decrypt_parser.add_argument('input', help='加密文件路径或文件夹')
    decrypt_parser.add_argument('output', help='输出文件路径或文件夹')
    decrypt_parser.add_argument('-p', '--password', help='解密密码（不提供则提示输入）')
    decrypt_parser.add_argument('--save-notice', action='store_true',
                               help='保存提示段（载体视频）到单独文件')
    decrypt_parser.add_argument('-a', '--algorithm', default='AES-CTR',
                               choices=['AES-CTR', 'AES-CBC', 'ChaCha20'],
                               help='加密算法（默认：自动检测）')
    decrypt_parser.add_argument('--batch', action='store_true',
                               help='批量解密模式（输入为文件夹）')
    decrypt_parser.add_argument('--pattern', default='*.enc.mp4',
                               help='批量解密时的文件匹配模式（默认：*.enc.mp4）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 获取密码
    password = args.password
    if not password:
        password = getpass.getpass("请输入密码: ")
    
    # 创建解密器
    decryptor = FileDecryptor(args.algorithm)
    
    # 执行解密
    if args.command == 'decrypt':
        # 检查是否是批量模式
        if os.path.isdir(args.input):
            # 批量解密
            if not os.path.exists(args.output):
                os.makedirs(args.output)
            
            import glob
            search_pattern = os.path.join(args.input, args.pattern)
            encrypted_files = glob.glob(search_pattern)
            
            if not encrypted_files:
                print(f"错误: 未找到匹配的加密文件: {search_pattern}")
                sys.exit(1)
            
            print(f"找到 {len(encrypted_files)} 个加密文件")
            print(f"输入目录: {args.input}")
            print(f"输出目录: {args.output}")
            print("-" * 50)
            
            success_count = 0
            failed_count = 0
            
            for i, encrypted_file in enumerate(encrypted_files, 1):
                relative_path = os.path.relpath(encrypted_file, args.input)
                output_filename = os.path.splitext(relative_path)[0] + ".mp4"
                output_path = os.path.join(args.output, output_filename)
                
                print(f"[{i}/{len(encrypted_files)}] 处理: {os.path.basename(encrypted_file)}")
                
                success, msg = decryptor.decrypt_to_file(
                    encrypted_file,
                    output_path,
                    password,
                    args.save_notice
                )
                
                if success:
                    success_count += 1
                    print(f"  ✓ {msg}")
                else:
                    failed_count += 1
                    print(f"  ✗ {msg}")
                print()
            
            print("=" * 50)
            print(f"批量解密完成")
            print(f"总文件数: {len(encrypted_files)}")
            print(f"成功: {success_count}")
            print(f"失败: {failed_count}")
            print(f"成功率: {(success_count/len(encrypted_files)*100):.1f}%")
            
            sys.exit(0 if failed_count == 0 else 1)
        
        else:
            # 单文件解密
            if not os.path.exists(args.input):
                print(f"错误: 输入文件不存在: {args.input}")
                sys.exit(1)
            
            success, msg = decryptor.decrypt_to_file(
                args.input,
                args.output,
                password,
                args.save_notice
            )
            
            if success:
                print(msg)
                sys.exit(0)
            else:
                print(msg)
                sys.exit(1)


if __name__ == "__main__":
    main()
