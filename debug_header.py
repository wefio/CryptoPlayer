#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player.file.encrypted_video import EncryptedVideoFile
from player.file.file_header import FileHeader

def debug_header(file_path):
    """调试加密文件头"""
    print(f"调试文件: {file_path}")
    print("=" * 60)
    
    try:
        # 加载文件
        encrypted_file = EncryptedVideoFile(file_path)
        
        print(f"文件大小: {os.path.getsize(file_path)} 字节")
        print(f"提示段大小: {len(encrypted_file.notice_data)} 字节")
        print(f"加密段大小: {len(encrypted_file.encrypted_data)} 字节")
        print()
        
        # 检查文件头
        header = encrypted_file.header
        print("文件头信息:")
        print(f"  魔数: {header.magic}")
        print(f"  版本: {header.version}")
        print(f"  记录的加密数据大小: {header.encrypted_size}")
        print(f"  实际加密数据大小: {len(encrypted_file.encrypted_data)}")
        print()
        
        # 检查加密信息
        info = header.get_encryption_info()
        print("加密信息:")
        print(f"  算法: {info.get('algorithm', 'N/A')}")
        print(f"  Salt: {info.get('salt', 'N/A')} (长度: {len(info.get('salt', b''))})")
        print(f"  IV/Nonce: {info.get('iv_nonce', 'N/A')} (长度: {len(info.get('iv_nonce', b''))})")
        print()
        
        # 检查reserved字段
        print("Reserved字段 (64字节):")
        print(f"  十六进制: {header.reserved.hex()}")
        print(f"  ASCII: {header.reserved.decode('ascii', errors='replace')}")
        print()
        
        # 验证完整性
        is_valid, msg = encrypted_file.verify_integrity()
        print(f"完整性验证: {'✓ 通过' if is_valid else '✗ 失败'}")
        print(f"  消息: {msg}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python debug_header.py <加密文件路径>")
        sys.exit(1)
    
    debug_header(sys.argv[1])
