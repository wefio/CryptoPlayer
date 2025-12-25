#!/usr/bin/env python3
# project_root/batch_encrypt.py - 批量加密脚本

import os
import sys
import glob
import argparse
import getpass
from pathlib import Path

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player.core.video_processor import VideoProcessor
from player.cli.interface import CLIInterface
from player.utils.file_utils import FileUtils
from player.exceptions.custom_exceptions import VideoEncryptionError


class BatchEncryptor:
    """批量加密器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化批量加密器
        
        Args:
            config_path: 配置文件路径
        """
        self.processor = VideoProcessor(config_path)
        self.cli = CLIInterface()
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def process_folder(self, input_folder: str, output_folder: str, 
                      password: str, notice_video_path: str = None,
                      metadata_config: str = None, pattern: str = "*.mp4",
                      recursive: bool = False, dry_run: bool = False,
                      pure_encrypt: bool = False, use_queue: bool = True):
        """
        处理文件夹中的所有视频
        
        Args:
            input_folder: 输入文件夹
            output_folder: 输出文件夹
            password: 加密密码
            notice_video_path: 提示视频路径
            metadata_config: 元数据配置文件路径
            pattern: 文件匹配模式
            recursive: 是否递归处理子文件夹
            dry_run: 试运行，不实际加密
            pure_encrypt: 纯加密模式（无提示段）
            use_queue: 是否使用队列文件夹（默认True）
            
        Returns:
            处理统计信息
        """
        # 检查队列文件夹
        queue_folder = None
        if use_queue:
            queue_folder = os.path.join(input_folder, "queue")
            if os.path.isdir(queue_folder):
                # 队列文件夹存在，使用批量模式
                print(f"检测到队列文件夹: queue")
                print(f"使用批量处理模式")
                input_folder = queue_folder
            else:
                print(f"未检测到队列文件夹，使用单文件处理模式")
        
        # 纯加密模式不使用元数据配置
        if pure_encrypt:
            metadata_config = None
        # 如果没有指定元数据配置，默认使用notice_assets/notice.txt
        elif metadata_config is None:
            metadata_config = "notice_assets/notice.txt"
            if not os.path.exists(metadata_config):
                metadata_config = None
        # 确保输出文件夹存在
        FileUtils.ensure_directory(output_folder)
        
        # 查找所有视频文件
        if recursive:
            search_pattern = os.path.join(input_folder, "**", pattern)
        else:
            search_pattern = os.path.join(input_folder, pattern)
        
        video_files = glob.glob(search_pattern, recursive=recursive)
        video_files.sort()
        
        self.stats['total'] = len(video_files)
        
        print(f"找到 {len(video_files)} 个视频文件")
        print(f"输入文件夹: {input_folder}")
        print(f"输出文件夹: {output_folder}")
        print(f"使用模式: {pattern}")
        print(f"递归搜索: {'是' if recursive else '否'}")
        print(f"试运行模式: {'是' if dry_run else '否'}")
        print("-" * 50)
        
        if dry_run:
            print("试运行模式，不会实际加密文件")
            for i, video_file in enumerate(video_files, 1):
                relative_path = os.path.relpath(video_file, input_folder)
                print(f"[{i}/{len(video_files)}] {relative_path}")
            print("-" * 50)
            print("试运行完成")
            return self.stats
        
        # 处理每个文件
        for i, video_file in enumerate(video_files, 1):
            try:
                # 获取相对路径以保持文件夹结构
                relative_path = os.path.relpath(video_file, input_folder)
                output_file = os.path.join(output_folder, relative_path)
                
                # 确保输出文件的目录存在
                output_dir = os.path.dirname(output_file)
                FileUtils.ensure_directory(output_dir)
                
                # 修改扩展名，添加.enc标识
                output_file = self._add_enc_suffix(output_file)
                
                print(f"[{i}/{len(video_files)}] 处理: {relative_path}")
                
                # 显示视频信息
                try:
                    self.cli.show_video_info(video_file)
                except Exception as e:
                    print(f"  警告: 无法获取视频信息: {e}")
                
                # 执行加密
                success = self.processor.encrypt_video(
                    input_path=video_file,
                    output_path=output_file,
                    password=password,
                    notice_video_path=notice_video_path,
                    metadata_config=metadata_config,
                    pure_encrypt=pure_encrypt
                )
                
                if success:
                    self.stats['success'] += 1
                    print(f"  ✓ 加密完成: {os.path.basename(output_file)}")
                    
                    # 显示输出文件信息
                    try:
                        self.cli.show_video_info(output_file)
                    except Exception as e:
                        print(f"  警告: 无法获取输出文件信息: {e}")
                else:
                    self.stats['failed'] += 1
                    print(f"  ✗ 加密失败: {os.path.basename(video_file)}")
                    
            except KeyboardInterrupt:
                print("\n用户中断操作")
                self.stats['skipped'] = len(video_files) - i + 1
                break
            except Exception as e:
                self.stats['failed'] += 1
                print(f"  ✗ 处理失败: {e}")
                import traceback
                traceback.print_exc()
            
            print()  # 空行分隔
        
        return self.stats
    
    def _add_enc_suffix(self, file_path: str) -> str:
        """
        为文件名添加.enc后缀
        
        Args:
            file_path: 文件路径
            
        Returns:
            添加后缀后的路径
        """
        path = Path(file_path)
        # 在扩展名前添加.enc
        new_name = f"{path.stem}.enc{path.suffix}"
        return str(path.with_name(new_name))
    
    def print_summary(self):
        """打印处理摘要"""
        print("=" * 50)
        print("批量加密完成")
        print("=" * 50)
        print(f"总文件数: {self.stats['total']}")
        print(f"成功: {self.stats['success']}")
        print(f"失败: {self.stats['failed']}")
        print(f"跳过: {self.stats['skipped']}")
        
        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            print(f"成功率: {success_rate:.1f}%")


def main():
    """批量加密主函数"""
    parser = argparse.ArgumentParser(description='批量加密视频文件')
    parser.add_argument('input_folder', help='输入文件夹路径')
    parser.add_argument('output_folder', help='输出文件夹路径')
    parser.add_argument('-p', '--password', help='加密密码（如果不提供，将从secrets/password.txt读取或提示输入）')
    parser.add_argument('-n', '--notice', help='提示视频路径（可选）')
    parser.add_argument('-m', '--metadata', help='元数据配置文件路径（可选）')
    parser.add_argument('--pure-encrypt', action='store_true',
                       help='纯加密模式（无提示段）')
    parser.add_argument('--pattern', default='*.mp4', 
                       help='文件匹配模式（默认：*.mp4）')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='递归处理子文件夹')
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行，不实际加密')
    parser.add_argument('--config', default='config.json',
                       help='配置文件路径（默认：config.json）')
    parser.add_argument('--confirm-password', action='store_true',
                       help='要求确认密码')
    parser.add_argument('--use-secrets', action='store_true',
                       help='从secrets/password.txt读取密码')
    parser.add_argument('--no-queue', action='store_true',
                       help='禁用队列文件夹功能')
    
    args = parser.parse_args()
    
    # 验证输入文件夹
    if not os.path.isdir(args.input_folder):
        print(f"错误: 输入文件夹不存在: {args.input_folder}")
        sys.exit(1)
    
    # 获取密码
    if args.password:
        password = args.password
        if args.confirm_password:
            confirm = getpass.getpass("请确认密码: ")
            if password != confirm:
                print("错误: 两次输入的密码不匹配")
                sys.exit(1)
    else:
        # 尝试从secrets/password.txt读取密码
        secrets_file = 'secrets/password.txt'
        if args.use_secrets and os.path.exists(secrets_file):
            with open(secrets_file, 'r', encoding='utf-8') as f:
                password = f.read().strip()
            print(f"已从文件读取密码: {secrets_file}")
        else:
            print("请输入加密密码:")
            password = getpass.getpass("密码: ")
            if args.confirm_password:
                confirm = getpass.getpass("确认密码: ")
                if password != confirm:
                    print("错误: 两次输入的密码不匹配")
                    sys.exit(1)
    
    # 验证提示视频（如果提供）
    if args.notice and not os.path.exists(args.notice):
        print(f"警告: 提示视频不存在: {args.notice}")
        args.notice = None
    
    # 验证元数据配置（如果提供）
    if args.metadata and not os.path.exists(args.metadata):
        print(f"警告: 元数据配置文件不存在: {args.metadata}")
        args.metadata = None
    
    # 创建批量加密器
    encryptor = BatchEncryptor(args.config)
    
    try:
        # 执行批量加密
        stats = encryptor.process_folder(
            input_folder=args.input_folder,
            output_folder=args.output_folder,
            password=password,
            notice_video_path=args.notice,
            metadata_config=args.metadata,
            pattern=args.pattern,
            recursive=args.recursive,
            dry_run=args.dry_run,
            pure_encrypt=args.pure_encrypt,
            use_queue=not args.no_queue
        )
        
        # 打印摘要
        encryptor.print_summary()
        
        # 如果有失败的文件，返回错误码
        if stats['failed'] > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"批量加密失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
