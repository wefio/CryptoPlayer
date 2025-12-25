#!/usr/bin/env python3
# test_features.py - 测试新功能

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player.core.video_processor import VideoProcessor

def test_password_from_file():
    """测试从文件读取密码"""
    print("测试1: 从文件读取密码")
    
    password_file = "secrets/password.txt"
    if os.path.exists(password_file):
        with open(password_file, 'r', encoding='utf-8') as f:
            password = f.read().strip()
        print(f"✓ 密码文件存在，密码: {password}")
    else:
        print("✗ 密码文件不存在")
    
    print()

def test_metadata_notice_text():
    """测试从notice_assets/notice.txt读取notice_text"""
    print("测试2: 从notice_assets/notice.txt读取notice_text")
    
    metadata_file = "notice_assets/notice.txt"
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('notice_text='):
                    notice_text = line.split('=', 1)[1]
                    print(f"✓ 找到notice_text")
                    print(f"  原始文本: {notice_text}")
                    print(f"  转换后: {notice_text.replace('\\n', chr(10))}")
                    break
    else:
        print("✗ notice_assets/notice.txt文件不存在")
    
    print()

def test_notice_videos():
    """测试提示视频资源"""
    print("测试3: 检查提示视频资源")
    
    notice_dir = "notice_assets"
    if os.path.exists(notice_dir):
        videos = [f for f in os.listdir(notice_dir) if f.endswith('.mp4')]
        if videos:
            print(f"✓ 找到 {len(videos)} 个提示视频:")
            for video in videos:
                print(f"  - {video}")
        else:
            print("✗ 未找到MP4视频文件")
    else:
        print("✗ notice_assets目录不存在")
    
    print()

def test_encryption():
    """测试加密功能"""
    print("测试4: 测试加密功能")
    
    input_file = "input_plain/input.mp4"
    output_file = "encrypted_output/input.enc.mp4"
    password_file = "secrets/password.txt"
    
    # 读取密码
    with open(password_file, 'r', encoding='utf-8') as f:
        password = f.read().strip()
    
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"使用密码: {password}")
    print(f"提示视频: 自动生成（基于notice_assets/notice.txt）")
    
    try:
        processor = VideoProcessor("config.json")
        success = processor.encrypt_video(
            input_path=input_file,
            output_path=output_file,
            password=password,
            notice_video_path=None,  # 自动生成
            metadata_config="notice_assets/notice.txt"
        )
        
        if success:
            print("✓ 加密成功")
            
            # 检查输出文件
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"  输出文件大小: {file_size:,} 字节")
            else:
                print("✗ 输出文件不存在")
        else:
            print("✗ 加密失败")
    except Exception as e:
        print(f"✗ 加密异常: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def test_decryption():
    """测试解密播放功能"""
    print("测试5: 测试解密播放功能")
    
    encrypted_file = "encrypted_output/input.enc.mp4"
    password_file = "secrets/password.txt"
    
    # 读取密码
    with open(password_file, 'r', encoding='utf-8') as f:
        password = f.read().strip()
    
    print(f"加密文件: {encrypted_file}")
    print(f"使用密码: {password}")
    print(f"跳过提示段: 是")
    
    try:
        processor = VideoProcessor("config.json")
        success = processor.decrypt_and_play(
            encrypted_path=encrypted_file,
            password=password,
            skip_notice=True  # 跳过提示段以节省测试时间
        )
        
        if success:
            print("✓ 解密播放成功")
        else:
            print("✗ 解密播放失败")
    except Exception as e:
        print(f"✗ 解密播放异常: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def main():
    """主函数"""
    print("=" * 60)
    print("  Shell Video Player - 功能测试")
    print("=" * 60)
    print()
    
    # 运行所有测试
    test_password_from_file()
    test_metadata_notice_text()
    test_notice_videos()
    test_encryption()
    print("注意: 解密播放测试需要手动关闭播放器窗口")
    input("按Enter键继续解密播放测试...")
    test_decryption()
    
    print("=" * 60)
    print("  所有测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
