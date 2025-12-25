#!/usr/bin/env python3
# batch_decrypt_save.py - 批量解密保存脚本

import os
import sys
import glob
import argparse
import getpass
from pathlib import Path

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player.core.decryptor import Decryptor
from player.file.encrypted_video import EncryptedVideoFile
from player.exceptions.custom_exceptions import CryptoError, FileFormatError


class BatchDecryptSaver:
    """批量解密保存器"""
    
    def __init__(self, algorithm: str = "AES-CTR"):
        """
        初始化批量解密保存器
        
        Args:
            algorithm: 加密算法
        """
        self.algorithm = algorithm
        self.decryptor = Decryptor(algorithm)
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
    
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
            
            # 检测MP4文件
            if encrypted_data[:4] == b'\x00\x00\x00\x18' or encrypted_data[:4] == b'\x00\x00\x00\x20':
                return '.mp4'
            
        except:
            pass
        
        # 默认返回.mp4
        return '.mp4'
    
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
            
            # 获取加密信息
            encryption_info = encrypted_file.header.get_encryption_info()
            algorithm = encryption_info.get('algorithm', 'N/A')
            
            # 解密数据
            encrypted_data = encrypted_file.extract_encrypted_section()
            decrypted_data = self.decryptor.decrypt_stream(encrypted_data, password, encryption_info)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 保存解密后的文件
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            # 保存提示段（载体视频）
            notice_output = None
            if save_notice and len(encrypted_file.notice_data) > 0:
                notice_output = os.path.splitext(output_path)[0] + "_notice.mp4"
                with open(notice_output, 'wb') as f:
                    f.write(encrypted_file.notice_data)
            
            return True, f"解密成功"
            
        except CryptoError as e:
            return False, f"解密失败: {e}"
        except Exception as e:
            return False, f"解密失败: {e}"
    
    def process_folder(self, input_folder: str, output_folder: str, password: str,
                      pattern: str = "*.enc.mp4", recursive: bool = False,
                      save_notice: bool = False, detect_type: bool = True,
                      skip_existing: bool = False, stop_on_error: bool = False):
        """
        处理文件夹中的所有加密文件
        
        Args:
            input_folder: 输入文件夹
            output_folder: 输出文件夹
            password: 解密密码
            pattern: 文件匹配模式
            recursive: 是否递归处理子文件夹
            save_notice: 是否保存提示段（载体视频）
            detect_type: 是否自动检测文件类型
            skip_existing: 是否跳过已存在的文件
            stop_on_error: 出错时是否停止
            
        Returns:
            处理统计信息
        """
        # 查找所有加密文件
        if recursive:
            search_pattern = os.path.join(input_folder, "**", pattern)
        else:
            search_pattern = os.path.join(input_folder, pattern)
        
        encrypted_files = glob.glob(search_pattern, recursive=recursive)
        encrypted_files.sort()
        
        self.stats['total'] = len(encrypted_files)
        
        print(f"找到 {len(encrypted_files)} 个加密文件")
        print(f"输入文件夹: {input_folder}")
        print(f"输出文件夹: {output_folder}")
        print(f"使用模式: {pattern}")
        print(f"递归搜索: {'是' if recursive else '否'}")
        print(f"自动检测文件类型: {'是' if detect_type else '否'}")
        print(f"保存提示段（载体视频）: {'是' if save_notice else '否'}")
        print(f"跳过已存在文件: {'是' if skip_existing else '否'}")
        print("-" * 50)
        
        # 确保输出文件夹存在
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # 处理每个文件
        for i, encrypted_file in enumerate(encrypted_files, 1):
            try:
                relative_path = os.path.relpath(encrypted_file, input_folder)
                print(f"[{i}/{len(encrypted_files)}] 处理: {relative_path}")
                
                # 加载加密文件获取信息
                encrypted_obj = EncryptedVideoFile(encrypted_file)
                
                # 显示文件信息
                print(f"  提示段大小: {len(encrypted_obj.notice_data)} 字节")
                print(f"  加密段大小: {len(encrypted_obj.encrypted_data)} 字节")
                
                encryption_info = encrypted_obj.header.get_encryption_info()
                print(f"  加密算法: {encryption_info.get('algorithm', 'N/A')}")
                
                # 确定输出文件名和扩展名
                filename_without_ext = os.path.splitext(os.path.basename(encrypted_file))[0]
                
                if detect_type:
                    # 尝试检测原始文件类型
                    ext = self.detect_original_extension(encrypted_obj)
                    print(f"  检测到文件类型: {ext}")
                else:
                    ext = '.mp4'  # 默认为.mp4
                
                output_filename = filename_without_ext + ext
                output_path = os.path.join(output_folder, output_filename)
                
                # 检查是否跳过已存在的文件
                if skip_existing and os.path.exists(output_path):
                    print(f"  ⊙ 文件已存在，跳过: {output_filename}")
                    self.stats['skipped'] += 1
                    continue
                
                # 执行解密
                print(f"  解密中...")
                success, msg = self.decrypt_to_file(
                    encrypted_file,
                    output_path,
                    password,
                    save_notice
                )
                
                if success:
                    self.stats['success'] += 1
                    print(f"  ✓ 解密成功: {output_filename}")
                    
                    if save_notice and len(encrypted_obj.notice_data) > 0:
                        notice_path = os.path.splitext(output_path)[0] + "_notice.mp4"
                        print(f"  ✓ 提示段已保存: {os.path.basename(notice_path)}")
                else:
                    self.stats['failed'] += 1
                    print(f"  ✗ 解密失败: {msg}")
                    
                    if stop_on_error:
                        print("出错时停止选项已启用，停止处理")
                        break
                    
                    # 询问是否继续
                    response = input("解密失败，是否继续？(y/n, 默认y): ").strip().lower()
                    if response == 'n' or response == 'no':
                        self.stats['skipped'] = len(encrypted_files) - i
                        print("用户选择停止处理")
                        break
                
                print()  # 空行分隔
            
            except KeyboardInterrupt:
                print("\n用户中断操作")
                self.stats['skipped'] = len(encrypted_files) - i + 1
                break
            except CryptoError as e:
                self.stats['failed'] += 1
                print(f"  ✗ 解密失败: {e}")
                
                if stop_on_error:
                    print("密码错误，停止处理")
                    break
                    
                # 询问是否重试
                response = input("密码错误，是否重试？(y/n, 默认n): ").strip().lower()
                if response == 'y' or response == 'yes':
                    i -= 1  # 重试当前文件
                else:
                    response = input("是否继续处理下一个文件？(y/n, 默认y): ").strip().lower()
                    if response == 'n' or response == 'no':
                        self.stats['skipped'] = len(encrypted_files) - i
                        print("用户选择停止处理")
                        break
            except Exception as e:
                self.stats['failed'] += 1
                print(f"  ✗ 处理失败: {e}")
                
                if stop_on_error:
                    print("出错时停止选项已启用，停止处理")
                    break
                
                import traceback
                traceback.print_exc()
                
                # 询问是否继续
                response = input("处理失败，是否继续？(y/n, 默认y): ").strip().lower()
                if response == 'n' or response == 'no':
                    self.stats['skipped'] = len(encrypted_files) - i
                    print("用户选择停止处理")
                    break
        
        return self.stats
    
    def print_summary(self):
        """打印处理摘要"""
        print("=" * 50)
        print("批量解密完成")
        print("=" * 50)
        print(f"总文件数: {self.stats['total']}")
        print(f"成功: {self.stats['success']}")
        print(f"失败: {self.stats['failed']}")
        print(f"跳过: {self.stats['skipped']}")
        
        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            print(f"成功率: {success_rate:.1f}%")


def main():
    """批量解密保存主函数"""
    parser = argparse.ArgumentParser(description='批量解密加密文件并保存到指定位置')
    parser.add_argument('input_folder', help='加密文件文件夹路径')
    parser.add_argument('output_folder', help='解密文件输出文件夹路径')
    parser.add_argument('-p', '--password', help='解密密码（不提供则从secrets/password.txt读取或提示输入）')
    parser.add_argument('--pattern', default='*.enc.mp4',
                       help='文件匹配模式（默认：*.enc.mp4）')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='递归处理子文件夹')
    parser.add_argument('--save-notice', action='store_true',
                       help='保存提示段（载体视频）到单独文件')
    parser.add_argument('--no-detect', action='store_true',
                       help='不自动检测文件类型（默认输出为.mp4）')
    parser.add_argument('--skip-existing', action='store_true',
                       help='跳过已存在的文件')
    parser.add_argument('--stop-on-error', action='store_true',
                       help='出错时停止处理')
    parser.add_argument('--use-secrets', action='store_true',
                       help='从secrets/password.txt读取密码')
    
    args = parser.parse_args()
    
    # 验证输入文件夹
    if not os.path.isdir(args.input_folder):
        print(f"错误: 输入文件夹不存在: {args.input_folder}")
        sys.exit(1)
    
    # 获取密码
    password = args.password
    if password is None:
        # 尝试从secrets/password.txt读取密码
        secrets_file = 'secrets/password.txt'
        if args.use_secrets and os.path.exists(secrets_file):
            with open(secrets_file, 'r', encoding='utf-8') as f:
                password = f.read().strip()
            print(f"已从文件读取密码: {secrets_file}")
        else:
            password = getpass.getpass("请输入密码: ")
    
    # 创建批量解密保存器
    decrypter = BatchDecryptSaver()
    
    try:
        # 执行批量解密
        stats = decrypter.process_folder(
            input_folder=args.input_folder,
            output_folder=args.output_folder,
            password=password,
            pattern=args.pattern,
            recursive=args.recursive,
            save_notice=args.save_notice,
            detect_type=not args.no_detect,
            skip_existing=args.skip_existing,
            stop_on_error=args.stop_on_error
        )
        
        # 打印摘要
        decrypter.print_summary()
        
        # 如果有失败的文件，返回错误码
        if stats['failed'] > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"批量解密失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
