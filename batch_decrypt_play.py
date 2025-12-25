#!/usr/bin/env python3
# project_root/batch_decrypt_play.py - 批量解密播放脚本

import os
import sys
import glob
import argparse
import getpass
import time
from pathlib import Path

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player.core.video_processor import VideoProcessor
from player.cli.interface import CLIInterface
from player.utils.file_utils import FileUtils
from player.exceptions.custom_exceptions import VideoEncryptionError, PasswordError


class BatchDecryptPlayer:
    """批量解密播放器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化批量解密播放器
        
        Args:
            config_path: 配置文件路径
        """
        self.processor = VideoProcessor(config_path)
        self.cli = CLIInterface()
        self.stats = {
            'total': 0,
            'played': 0,
            'failed': 0,
            'skipped': 0
        }
        self.current_password = None
    
    def process_folder(self, input_folder: str, password: str = None,
                      pattern: str = "*.enc.mp4", recursive: bool = False,
                      skip_all_notice: bool = False, ask_each: bool = False,
                      stop_on_error: bool = False, playlist_mode: bool = False,
                      shuffle: bool = False):
        """
        处理文件夹中的所有加密视频
        
        Args:
            input_folder: 输入文件夹
            password: 解密密码（如果不提供，将为每个文件提示）
            pattern: 文件匹配模式
            recursive: 是否递归处理子文件夹
            skip_all_notice: 是否跳过所有提示段
            ask_each: 是否为每个文件单独询问
            stop_on_error: 出错时是否停止
            playlist_mode: 播放列表模式（连续播放）
            shuffle: 随机播放
            
        Returns:
            处理统计信息
        """
        # 查找所有加密视频文件
        if recursive:
            search_pattern = os.path.join(input_folder, "**", pattern)
        else:
            search_pattern = os.path.join(input_folder, pattern)
        
        video_files = glob.glob(search_pattern, recursive=recursive)
        video_files.sort()
        
        self.stats['total'] = len(video_files)
        
        print(f"找到 {len(video_files)} 个加密视频文件")
        print(f"输入文件夹: {input_folder}")
        print(f"使用模式: {pattern}")
        print(f"递归搜索: {'是' if recursive else '否'}")
        print(f"播放列表模式: {'是' if playlist_mode else '否'}")
        print(f"随机播放: {'是' if shuffle else '否'}")
        print("-" * 50)
        
        if shuffle:
            import random
            random.shuffle(video_files)
        
        # 处理每个文件
        for i, video_file in enumerate(video_files, 1):
            try:
                relative_path = os.path.relpath(video_file, input_folder)
                print(f"[{i}/{len(video_files)}] 准备播放: {relative_path}")
                
                # 显示视频信息
                try:
                    self.cli.show_video_info(video_file)
                except Exception as e:
                    print(f"  警告: 无法获取视频信息: {e}")
                
                # 获取密码
                file_password = password
                if file_password is None:
                    if self.current_password is None or ask_each:
                        print(f"请输入 {os.path.basename(video_file)} 的解密密码:")
                        file_password = getpass.getpass("密码: ")
                        if not ask_each:
                            self.current_password = file_password
                    else:
                        file_password = self.current_password
                
                # 询问是否跳过提示段（仅在存在提示段时询问）
                skip_notice = skip_all_notice
                if not skip_all_notice and not playlist_mode:
                    # 检查是否有提示段
                    from player.file.encrypted_video import EncryptedVideoFile
                    encrypted_file = EncryptedVideoFile(video_file)
                    has_notice = encrypted_file.notice_data is not None and len(encrypted_file.notice_data) > 0
                    
                    if has_notice:
                        response = input("是否跳过提示段？(y/n, 默认n): ").strip().lower()
                        skip_notice = response == 'y' or response == 'yes'
                    else:
                        skip_notice = True  # 无提示段，直接跳过
                
                # 执行解密播放
                print(f"开始播放...")
                success = self.processor.decrypt_and_play(
                    encrypted_path=video_file,
                    password=file_password,
                    skip_notice=skip_notice
                )
                
                if success:
                    self.stats['played'] += 1
                    print(f"  ✓ 播放完成")
                    
                    # 如果不是播放列表模式，询问是否继续
                    if not playlist_mode and i < len(video_files):
                        response = input("是否继续播放下一个文件？(y/n, 默认y): ").strip().lower()
                        if response == 'n' or response == 'no':
                            self.stats['skipped'] = len(video_files) - i
                            print("用户选择停止播放")
                            break
                else:
                    self.stats['failed'] += 1
                    print(f"  ✗ 播放失败")
                    
                    if stop_on_error:
                        print("出错时停止选项已启用，停止播放")
                        break
                    
                    # 询问是否继续
                    response = input("播放失败，是否继续？(y/n, 默认y): ").strip().lower()
                    if response == 'n' or response == 'no':
                        self.stats['skipped'] = len(video_files) - i
                        print("用户选择停止播放")
                        break
                
                # 播放列表模式下，在文件之间添加短暂间隔
                if playlist_mode and i < len(video_files):
                    print(f"下一个视频将在5秒后开始...")
                    for remaining in range(5, 0, -1):
                        print(f"\r{remaining}秒...", end='')
                        time.sleep(1)
                    print("\r开始下一个视频...")
                    
            except KeyboardInterrupt:
                print("\n用户中断操作")
                self.stats['skipped'] = len(video_files) - i + 1
                break
            except PasswordError as e:
                self.stats['failed'] += 1
                self.cli.show_error(e)
                
                if stop_on_error:
                    print("密码错误，停止播放")
                    break
                    
                # 询问是否重试
                response = input("密码错误，是否重试？(y/n, 默认n): ").strip().lower()
                if response == 'y' or response == 'yes':
                    i -= 1  # 重试当前文件
                else:
                    response = input("是否继续播放下一个文件？(y/n, 默认y): ").strip().lower()
                    if response == 'n' or response == 'no':
                        self.stats['skipped'] = len(video_files) - i
                        break
            except Exception as e:
                self.stats['failed'] += 1
                print(f"  ✗ 处理失败: {e}")
                
                if stop_on_error:
                    print("出错时停止选项已启用，停止播放")
                    break
                
                import traceback
                traceback.print_exc()
                
                # 询问是否继续
                response = input("处理失败，是否继续？(y/n, 默认y): ").strip().lower()
                if response == 'n' or response == 'no':
                    self.stats['skipped'] = len(video_files) - i
                    print("用户选择停止播放")
                    break
            
            print()  # 空行分隔
        
        return self.stats
    
    def print_summary(self):
        """打印处理摘要"""
        print("=" * 50)
        print("批量播放完成")
        print("=" * 50)
        print(f"总文件数: {self.stats['total']}")
        print(f"已播放: {self.stats['played']}")
        print(f"失败: {self.stats['failed']}")
        print(f"跳过: {self.stats['skipped']}")
        
        if self.stats['total'] > 0:
            success_rate = (self.stats['played'] / self.stats['total']) * 100
            print(f"播放成功率: {success_rate:.1f}%")


def main():
    """批量解密播放主函数"""
    parser = argparse.ArgumentParser(description='批量解密播放视频文件')
    parser.add_argument('input_folder', help='加密视频文件夹路径')
    parser.add_argument('-p', '--password', help='解密密码（如果不提供，将从secrets/password.txt读取或提示输入）')
    parser.add_argument('--pattern', default='*.enc.mp4', 
                       help='文件匹配模式（默认：*.enc.mp4）')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='递归处理子文件夹')
    parser.add_argument('--skip-notice', action='store_true',
                       help='跳过所有提示段')
    parser.add_argument('--ask-each', action='store_true',
                       help='为每个文件单独询问密码')
    parser.add_argument('--stop-on-error', action='store_true',
                       help='出错时停止播放')
    parser.add_argument('--playlist', action='store_true',
                       help='播放列表模式（连续播放）')
    parser.add_argument('--shuffle', action='store_true',
                       help='随机播放')
    parser.add_argument('--config', default='config.json',
                       help='配置文件路径（默认：config.json）')
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
    
    # 创建批量解密播放器
    player = BatchDecryptPlayer(args.config)
    
    try:
        # 执行批量播放
        stats = player.process_folder(
            input_folder=args.input_folder,
            password=args.password,
            pattern=args.pattern,
            recursive=args.recursive,
            skip_all_notice=args.skip_notice,
            ask_each=args.ask_each,
            stop_on_error=args.stop_on_error,
            playlist_mode=args.playlist,
            shuffle=args.shuffle
        )
        
        # 打印摘要
        player.print_summary()
        
        # 如果有失败的文件，返回错误码
        if stats['failed'] > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"批量播放失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
