#!/usr/bin/env python3
# interactive_tool.py - 交互式加解密一体化工具

import os
import sys
import getpass
from pathlib import Path

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player.core.video_processor import VideoProcessor
from player.cli.interface import CLIInterface
from player.utils.file_utils import FileUtils


class InteractiveTool:
    """交互式加解密工具"""
    
    def __init__(self):
        """初始化交互式工具"""
        self.processor = VideoProcessor()
        self.cli = CLIInterface()
        self.password = None
        self.notice_video_path = None
        self.metadata_config = "notice_assets/notice.txt"
        self.secrets_password_path = "secrets/password.txt"
        self.algorithm = "AES-CTR"  # 默认加密算法
        
        # 可用的加密算法
        self.available_algorithms = ["AES-CTR", "AES-CBC", "ChaCha20"]
    
    def load_password_from_file(self):
        """从文件加载密码"""
        if os.path.exists(self.secrets_password_path):
            with open(self.secrets_password_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
    
    def ask_password(self, operation="操作"):
        """询问密码"""
        # 先尝试从文件加载
        file_password = self.load_password_from_file()
        
        print(f"\n{'='*50}")
        print(f"  {operation}密码设置")
        print(f"{'='*50}")
        
        if file_password:
            print(f"检测到密码文件: {self.secrets_password_path}")
            print(f"文件中的密码: {file_password}")
            
            choice = input("\n是否使用文件中的密码？(y/n, 默认y): ").strip().lower()
            if choice == '' or choice == 'y':
                self.password = file_password
                print(f"✓ 已使用文件中的密码")
                return
        
        # 手动输入密码
        self.password = getpass.getpass(f"请输入{operation}密码: ")
        confirm = getpass.getpass("确认密码: ")
        
        if self.password != confirm:
            print("✗ 两次输入的密码不匹配")
            sys.exit(1)
        
        # 询问是否保存密码
        save_choice = input("\n是否保存密码到文件以便下次使用？(y/n, 默认n): ").strip().lower()
        if save_choice == 'y':
            self.save_password_to_file()
    
    def save_password_to_file(self):
        """保存密码到文件"""
        os.makedirs(os.path.dirname(self.secrets_password_path), exist_ok=True)
        with open(self.secrets_password_path, 'w', encoding='utf-8') as f:
            f.write(self.password)
        print(f"✓ 密码已保存到: {self.secrets_password_path}")
    
    def select_notice_video(self):
        """选择提示视频"""
        print(f"\n{'='*50}")
        print("  选择提示视频")
        print(f"{'='*50}")
        
        notice_dir = "notice_assets"
        available_videos = []
        
        if os.path.exists(notice_dir):
            for file in os.listdir(notice_dir):
                if file.endswith('.mp4') and not file.startswith('.'):
                    available_videos.append(os.path.join(notice_dir, file))
        
        if available_videos:
            print("\n可用提示视频:")
            for i, video in enumerate(available_videos, 1):
                print(f"  [{i}] {os.path.basename(video)}")
            print(f"  [0] 自动生成（使用metadata.txt中的文本）")
            
            choice = input(f"\n请选择提示视频 (0-{len(available_videos)}, 默认0): ").strip()
            
            try:
                idx = int(choice) if choice else 0
                if 0 < idx <= len(available_videos):
                    self.notice_video_path = available_videos[idx-1]
                    print(f"✓ 已选择: {os.path.basename(self.notice_video_path)}")
                    return
            except ValueError:
                pass
        
        # 默认：自动生成
        print("✓ 将自动生成提示视频（使用metadata.txt中的文本）")
        self.notice_video_path = None
    
    def encrypt_single_file(self):
        """加密单个文件"""
        print(f"\n{'='*50}")
        print("  单文件加密")
        print(f"{'='*50}")
        
        # 列出input_plain目录中的视频文件和通用文件
        input_dir = "input_plain"
        available_videos = []
        available_files = []
        queue_files = []
        queue_folder = os.path.join(input_dir, "queue")
        
        if os.path.exists(input_dir):
            for file in os.listdir(input_dir):
                file_path = os.path.join(input_dir, file)
                if os.path.isdir(file_path):
                    continue
                if not file.startswith('.'):
                    if file.endswith('.mp4'):
                        available_videos.append(file_path)
                    else:
                        available_files.append(file_path)
        
        # 检查队列文件夹
        if os.path.exists(queue_folder) and os.path.isdir(queue_folder):
            for file in os.listdir(queue_folder):
                if file.endswith('.mp4') and not file.startswith('.'):
                    queue_files.append(os.path.join(queue_folder, file))
        
        # 选择输入文件
        if available_videos or available_files or queue_files:
            print("\n可用文件:")
            
            current_idx = 1
            
            # 列出视频文件
            if available_videos:
                print("\n视频文件:")
                for i, video in enumerate(available_videos, current_idx):
                    print(f"  [{i}] {os.path.basename(video)}")
                current_idx += len(available_videos)
            
            # 列出其他文件（用于隐写术）
            if available_files:
                print("\n其他文件（用于隐写术）:")
                for i, file in enumerate(available_files, current_idx):
                    print(f"  [{i}] {os.path.basename(file)}")
                current_idx += len(available_files)
            
            # 列出队列文件夹选项
            if queue_files:
                queue_idx = current_idx
                print(f"\n  [{queue_idx}] 队列文件夹 文件数量：{len(queue_files)}")
                current_idx += 1
            
            print(f"\n  [0] 手动输入路径")
            
            max_choice = current_idx - 1
            choice = input(f"\n请选择要加密的文件 (0-{max_choice}, 默认1): ").strip()
            
            try:
                idx = int(choice) if choice else 1
                if 0 < idx <= len(available_videos):
                    input_path = available_videos[idx-1]
                    print(f"✓ 已选择: {os.path.basename(input_path)}")
                    is_video = True
                elif idx > len(available_videos) and idx <= len(available_videos) + len(available_files):
                    input_path = available_files[idx - len(available_videos) - 1]
                    print(f"✓ 已选择: {os.path.basename(input_path)}")
                    is_video = False
                elif queue_files and idx == queue_idx:
                    # 选择了队列文件夹，进行批量加密
                    return self.encrypt_batch_from_queue(queue_files)
                elif idx == 0:
                    input_path = input("\n请输入要加密的文件路径: ").strip().strip('"')
                    if not os.path.exists(input_path):
                        print(f"✗ 文件不存在: {input_path}")
                        return False
                    is_video = input_path.lower().endswith('.mp4')
                else:
                    print("✗ 无效的选择")
                    return False
            except ValueError:
                print("✗ 无效的输入")
                return False
        else:
            input_path = input("\n请输入要加密的视频文件路径: ").strip().strip('"')
            if not os.path.exists(input_path):
                print(f"✗ 文件不存在: {input_path}")
                return False
        
        # 选择加密算法
        print(f"\n{'='*50}")
        print("  选择加密算法")
        print(f"{'='*50}")
        print("\n可用加密算法:")
        for i, algo in enumerate(self.available_algorithms, 1):
            print(f"  [{i}] {algo}")
        
        choice = input(f"\n请选择加密算法 (1-{len(self.available_algorithms)}, 默认1): ").strip()
        try:
            idx = int(choice) if choice else 1
            if 1 <= idx <= len(self.available_algorithms):
                self.algorithm = self.available_algorithms[idx-1]
                print(f"✓ 已选择: {self.algorithm}")
            else:
                print(f"✗ 无效的选择，使用默认算法: {self.algorithm}")
        except ValueError:
            print(f"✗ 无效的输入，使用默认算法: {self.algorithm}")
        
        # 更新加密器算法
        from player.core.crypto_factory import CryptoAlgorithmFactory
        factory = CryptoAlgorithmFactory()
        self.processor.encryptor.crypto_algorithm = factory.create_algorithm(self.algorithm)
        self.processor.encryptor.algorithm = self.algorithm
        
        # 询问是否使用纯加密模式
        pure_encrypt = input(f"\n使用纯加密模式（无提示段）？(y/n, 默认n): ").strip().lower()
        pure_encrypt = (pure_encrypt == 'y')
        
        # 选择输出文件
        # 默认输出到encrypted_output目录
        output_dir = "encrypted_output"
        os.makedirs(output_dir, exist_ok=True)
        
        input_filename = os.path.basename(input_path)
        default_output = os.path.join(output_dir, os.path.splitext(input_filename)[0] + ".enc.mp4")
        output_path = input(f"输出文件路径 (默认: {default_output}): ").strip().strip('"')
        if not output_path:
            output_path = default_output
        
        # 选择提示视频（仅在非纯加密模式下）
        notice_video = None
        use_metadata = False
        if not pure_encrypt:
            self.select_notice_video()
            notice_video = self.notice_video_path
            
            # 询问是否使用metadata
            use_metadata = input(f"\n使用metadata.txt作为提示内容？(y/n, 默认y): ").strip().lower()
            use_metadata = (use_metadata == '' or use_metadata == 'y')
            if use_metadata and os.path.exists(self.metadata_config):
                print(f"✓ 将使用: {self.metadata_config}")
            else:
                print(f"✗ 文件不存在: {self.metadata_config}")
                self.metadata_config = None
        
        # 显示加密信息
        print(f"\n{'='*50}")
        print("  加密信息确认")
        print(f"{'='*50}")
        print(f"输入文件: {input_path}")
        print(f"输出文件: {output_path}")
        print(f"加密算法: {self.algorithm}")
        if self.notice_video_path:
            print(f"提示视频: {os.path.basename(self.notice_video_path)}")
        else:
            print(f"提示视频: 自动生成（基于metadata.txt）")
        if self.metadata_config:
            print(f"元数据配置: {self.metadata_config}")
        
        confirm = input("\n确认加密？(y/n, 默认y): ").strip().lower()
        if confirm != '' and confirm != 'y':
            print("已取消加密")
            return False
        
        # 执行加密
        try:
            success = self.processor.encrypt_video(
                input_path=input_path,
                output_path=output_path,
                password=self.password,
                notice_video_path=self.notice_video_path,
                metadata_config=self.metadata_config
            )
            
            if success:
                print(f"\n✓ 加密成功!")
                print(f"  输出文件: {output_path}")
                return True
            else:
                print(f"\n✗ 加密失败")
                return False
        except Exception as e:
            print(f"\n✗ 加密失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def encrypt_batch_from_queue(self, queue_files):
        """批量加密队列文件夹中的文件"""
        print(f"\n{'='*50}")
        print("  批量加密队列文件")
        print(f"{'='*50}")
        print(f"队列文件数量: {len(queue_files)}")
        
        # 选择加密算法
        print(f"\n{'='*50}")
        print("  选择加密算法")
        print(f"{'='*50}")
        print("\n可用加密算法:")
        for i, algo in enumerate(self.available_algorithms, 1):
            print(f"  [{i}] {algo}")
        
        choice = input(f"\n请选择加密算法 (1-{len(self.available_algorithms)}, 默认1): ").strip()
        try:
            idx = int(choice) if choice else 1
            if 1 <= idx <= len(self.available_algorithms):
                self.algorithm = self.available_algorithms[idx-1]
                print(f"✓ 已选择: {self.algorithm}")
            else:
                print(f"✗ 无效的选择，使用默认算法: {self.algorithm}")
        except ValueError:
            print(f"✗ 无效的输入，使用默认算法: {self.algorithm}")
        
        # 更新加密器算法
        from player.core.crypto_factory import CryptoAlgorithmFactory
        factory = CryptoAlgorithmFactory()
        self.processor.encryptor.crypto_algorithm = factory.create_algorithm(self.algorithm)
        self.processor.encryptor.algorithm = self.algorithm
        
        # 询问是否纯加密模式
        pure_encrypt = input(f"\n使用纯加密模式（无提示段）？(y/n, 默认n): ").strip().lower()
        pure_encrypt = (pure_encrypt == 'y')
        
        # 选择输出目录
        output_dir = "encrypted_output"
        os.makedirs(output_dir, exist_ok=True)
        
        default_output = output_dir
        output_path = input(f"输出目录 (默认: {default_output}): ").strip().strip('"')
        if output_path:
            output_dir = output_path
            os.makedirs(output_dir, exist_ok=True)
        
        # 选择提示视频（仅在非纯加密模式下）
        use_metadata = False
        if not pure_encrypt:
            self.select_notice_video()
            
            # 询问是否使用metadata
            use_metadata = input(f"\n使用metadata.txt作为提示内容？(y/n, 默认y): ").strip().lower()
            use_metadata = (use_metadata == '' or use_metadata == 'y')
            if use_metadata and os.path.exists(self.metadata_config):
                print(f"✓ 将使用: {self.metadata_config}")
            else:
                print(f"✗ 文件不存在: {self.metadata_config}")
                self.metadata_config = None
        
        # 显示加密信息
        print(f"\n{'='*50}")
        print("  批量加密信息确认")
        print(f"{'='*50}")
        print(f"队列文件数量: {len(queue_files)}")
        print(f"输出目录: {output_dir}")
        print(f"加密算法: {self.algorithm}")
        if pure_encrypt:
            print(f"加密模式: 纯加密（无提示段）")
        else:
            if self.notice_video_path:
                print(f"提示视频: {os.path.basename(self.notice_video_path)}")
            else:
                print(f"提示视频: 自动生成（基于metadata.txt）")
            if use_metadata and self.metadata_config:
                print(f"元数据配置: {self.metadata_config}")
        
        print("\n队列文件列表:")
        for i, file in enumerate(queue_files, 1):
            print(f"  [{i}] {os.path.basename(file)}")
        
        confirm = input("\n确认批量加密？(y/n, 默认y): ").strip().lower()
        if confirm != '' and confirm != 'y':
            print("已取消批量加密")
            return False
        
        # 执行批量加密
        print(f"\n{'='*50}")
        print("  开始批量加密")
        print(f"{'='*50}")
        
        success_count = 0
        failed_count = 0
        
        for i, input_file in enumerate(queue_files, 1):
            try:
                print(f"\n[{i}/{len(queue_files)}] 处理: {os.path.basename(input_file)}")
                
                # 生成输出文件名
                input_filename = os.path.basename(input_file)
                output_file = os.path.join(output_dir, os.path.splitext(input_filename)[0] + ".enc.mp4")
                
                # 执行加密
                success = self.processor.encrypt_video(
                    input_path=input_file,
                    output_path=output_file,
                    password=self.password,
                    notice_video_path=self.notice_video_path if not pure_encrypt else None,
                    metadata_config=self.metadata_config if use_metadata else None,
                    pure_encrypt=pure_encrypt
                )
                
                if success:
                    success_count += 1
                    print(f"  ✓ 加密成功")
                else:
                    failed_count += 1
                    print(f"  ✗ 加密失败")
                    
            except Exception as e:
                failed_count += 1
                print(f"  ✗ 加密失败: {e}")
        
        # 显示结果
        print(f"\n{'='*50}")
        print("  批量加密完成")
        print(f"{'='*50}")
        print(f"总文件数: {len(queue_files)}")
        print(f"成功: {success_count}")
        print(f"失败: {failed_count}")
        print(f"成功率: {(success_count/len(queue_files)*100):.1f}%")
        
        return success_count > 0
    
    def decrypt_and_play_single_file(self):
        """解密并播放单个文件"""
        print(f"\n{'='*50}")
        print("  解密播放")
        print(f"{'='*50}")
        
        # 列出encrypted_output目录中的加密视频文件
        input_dir = "encrypted_output"
        available_videos = []
        
        if os.path.exists(input_dir):
            for file in os.listdir(input_dir):
                if file.endswith('.enc.mp4') and not file.startswith('.'):
                    available_videos.append(os.path.join(input_dir, file))
        
        # 选择输入文件
        if available_videos:
            print("\n可用加密视频文件:")
            for i, video in enumerate(available_videos, 1):
                print(f"  [{i}] {os.path.basename(video)}")
            print(f"  [0] 手动输入路径")
            
            choice = input(f"\n请选择要播放的视频 (0-{len(available_videos)}, 默认1): ").strip()
            
            try:
                idx = int(choice) if choice else 1
                if 0 < idx <= len(available_videos):
                    input_path = available_videos[idx-1]
                    print(f"✓ 已选择: {os.path.basename(input_path)}")
                elif idx == 0:
                    input_path = input("\n请输入加密视频文件路径: ").strip().strip('"')
                    if not os.path.exists(input_path):
                        print(f"✗ 文件不存在: {input_path}")
                        return False
                else:
                    print("✗ 无效的选择")
                    return False
            except ValueError:
                print("✗ 无效的输入")
                return False
        else:
            input_path = input("\n请输入加密视频文件路径: ").strip().strip('"')
            if not os.path.exists(input_path):
                print(f"✗ 文件不存在: {input_path}")
                return False
        
        # 检测加密文件类型
        from player.file.encrypted_video import EncryptedVideoFile
        encrypted_file = EncryptedVideoFile(input_path)
        has_notice = encrypted_file.notice_data is not None and len(encrypted_file.notice_data) > 0
        
        # 检测是否可能是隐写文件（通过文件名判断）
        filename = os.path.basename(input_path)
        is_steganography = False
        
        # 方法1：检查文件名中是否包含常见文件扩展名
        if any(x in filename.lower() for x in ['zip', 'rar', '7z', 'pdf', 'doc', 'txt', 'image', 'portable']):
            is_steganography = True
        
        # 方法2：如果文件以.enc.mp4结尾但不是视频加密，可能是隐写
        # 检查原始文件名（去掉.enc.mp4）是否包含常见扩展名
        if filename.endswith('.enc.mp4'):
            base_name = filename[:-8]  # 去掉 .enc.mp4
            if any(x in base_name.lower() for x in ['zip', 'rar', '7z', 'pdf', 'doc', 'txt', 'image']):
                is_steganography = True
        
        # 方法3：检查文件名格式是否为：filename.type.enc.mp4（隐写模式）
        if filename.count('.') >= 2 and 'enc.mp4' in filename:
            base_part = filename.replace('.enc.mp4', '')
            if '.' in base_part:  # 例如: wiztree_4_25_portable.zip.enc.mp4
                is_steganography = True
        
        # 如果检测到可能是隐写文件，提供提示
        if is_steganography:
            print(f"\n{'='*50}")
            print("  ⚠ 提示：这可能是一个隐写文件")
            print(f"{'='*50}")
            print(f"  此文件可能包含非视频内容（如ZIP、文档、图片等）")
            print(f"  建议操作：")
            print(f"    1. 使用 [3] 解密保存 功能解密文件")
            print(f"    2. 解密后根据需要修改文件扩展名（如改为.zip）")
            print(f"    3. 如果仍要播放，继续下方操作")
            print(f"{'='*50}")
            
            confirm = input("\n是否继续播放？(y/n, 默认n): ").strip().lower()
            if confirm != 'y' and confirm != 'yes':
                print("已取消播放，建议使用 [3] 解密保存 功能")
                return False
        
        # 询问是否跳过提示段（仅在存在提示段时询问）
        skip_notice = False
        if has_notice:
            skip_notice = input("\n是否跳过提示段？(y/n, 默认n): ").strip().lower()
            skip_notice = (skip_notice == 'y')
        else:
            print("  检测到无提示段，将直接播放加密内容")
        
        # 执行解密播放
        try:
            success = self.processor.decrypt_and_play(
                encrypted_path=input_path,
                password=self.password,
                skip_notice=skip_notice
            )
            
            if success:
                print(f"\n✓ 播放完成")
                return True
            else:
                print(f"\n✗ 播放失败")
                return False
        except Exception as e:
            print(f"\n✗ 播放失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def decrypt_and_save_file(self):
        """解密并保存文件"""
        print(f"\n{'='*50}")
        print("  解密保存")
        print(f"{'='*50}")
        
        # 列出encrypted_output目录中的加密视频文件
        input_dir = "encrypted_output"
        available_videos = []
        
        if os.path.exists(input_dir):
            for file in os.listdir(input_dir):
                if file.endswith('.enc.mp4') and not file.startswith('.'):
                    available_videos.append(os.path.join(input_dir, file))
        
        # 选择输入文件
        if available_videos:
            print("\n可用加密视频文件:")
            for i, video in enumerate(available_videos, 1):
                print(f"  [{i}] {os.path.basename(video)}")
            print(f"  [0] 手动输入路径")
            
            choice = input(f"\n请选择要解密的文件 (0-{len(available_videos)}, 默认1): ").strip()
            
            try:
                idx = int(choice) if choice else 1
                if 0 < idx <= len(available_videos):
                    input_path = available_videos[idx-1]
                    print(f"✓ 已选择: {os.path.basename(input_path)}")
                elif idx == 0:
                    input_path = input("\n请输入加密视频文件路径: ").strip().strip('"')
                    if not os.path.exists(input_path):
                        print(f"✗ 文件不存在: {input_path}")
                        return False
                else:
                    print("✗ 无效的选择")
                    return False
            except ValueError:
                print("✗ 无效的输入")
                return False
        else:
            input_path = input("\n请输入加密视频文件路径: ").strip().strip('"')
            if not os.path.exists(input_path):
                print(f"✗ 文件不存在: {input_path}")
                return False
        
        # 选择输出文件
        input_filename = os.path.basename(input_path)
        base_filename = os.path.splitext(input_filename)[0]
        default_output = os.path.join("decrypted_output", base_filename + ".mp4")
        output_path = input(f"输出文件路径 (默认: {default_output}): ").strip().strip('"')
        if not output_path:
            output_path = default_output
        
        # 询问是否保存提示段（载体视频）
        save_notice = input("\n是否保存提示段（载体视频）？(y/n, 默认n): ").strip().lower()
        save_notice = (save_notice == 'y')
        
        # 执行解密
        try:
            from player.core.decryptor import Decryptor
            from player.file.encrypted_video import EncryptedVideoFile
            
            print(f"\n开始解密...")
            
            # 加载加密文件
            encrypted_file = EncryptedVideoFile(input_path)
            
            print(f"提示段大小: {len(encrypted_file.notice_data)} 字节")
            print(f"加密段大小: {len(encrypted_file.encrypted_data)} 字节")
            
            # 获取加密信息
            encryption_info = encrypted_file.header.get_encryption_info()
            print(f"加密算法: {encryption_info.get('algorithm', 'N/A')}")
            
            # 解密数据
            decryptor = Decryptor()
            encrypted_data = encrypted_file.extract_encrypted_section()
            decrypted_data = decryptor.decrypt_stream(encrypted_data, self.password, encryption_info)
            print(f"✓ 解密完成，解密后大小: {len(decrypted_data)} 字节")
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 保存解密后的文件
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            print(f"✓ 解密文件已保存: {output_path}")
            
            # 保存提示段（载体视频）
            if save_notice and len(encrypted_file.notice_data) > 0:
                notice_output = os.path.splitext(output_path)[0] + "_notice.mp4"
                with open(notice_output, 'wb') as f:
                    f.write(encrypted_file.notice_data)
                print(f"✓ 提示段（载体视频）已保存: {notice_output}")
            
            return True
            
        except Exception as e:
            print(f"\n✗ 解密失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_menu(self):
        """显示主菜单"""
        while True:
            print(f"\n{'='*50}")
            print("  Shell Video Player - 交互式工具")
            print(f"{'='*50}")
            print("  [1] 加密视频")
            print("  [2] 解密播放")
            print("  [3] 解密保存")
            print("  [4] 设置密码")
            print("  [5] 退出")
            print(f"{'='*50}")
            
            choice = input("\n请选择操作 (1-5): ").strip()
            
            if choice == '1':
                # 加密视频
                if not self.password:
                    self.ask_password("加密")
                self.encrypt_single_file()
                
            elif choice == '2':
                # 解密播放
                if not self.password:
                    self.ask_password("解密")
                self.decrypt_and_play_single_file()
                
            elif choice == '3':
                # 解密保存
                if not self.password:
                    self.ask_password("解密")
                self.decrypt_and_save_file()
                
            elif choice == '4':
                # 设置密码
                self.ask_password()
                
            elif choice == '5':
                # 退出
                print("\n再见!")
                sys.exit(0)
                
            else:
                print("\n✗ 无效的选择")


def main():
    """主函数"""
    try:
        tool = InteractiveTool()
        tool.show_menu()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
