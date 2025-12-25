#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player.file.encrypted_video import EncryptedVideoFile
from player.core.decryptor import Decryptor
from player.core.encryptor import Encryptor

def test_decrypt(file_path, password):
    """测试解密流程"""
    print(f"测试文件: {file_path}")
    print(f"密码: {password}")
    print("=" * 60)
    
    try:
        # 步骤1: 加载文件
        print("\n[步骤1] 加载加密文件...")
        encrypted_file = EncryptedVideoFile(file_path)
        print(f"✓ 文件加载成功")
        print(f"  提示段大小: {len(encrypted_file.notice_data)}")
        print(f"  加密段大小: {len(encrypted_file.encrypted_data)}")
        
        # 步骤2: 获取加密信息
        print("\n[步骤2] 获取加密信息...")
        encryption_info = encrypted_file.header.get_encryption_info()
        print(f"  加密信息字典: {encryption_info}")
        print(f"  算法: {encryption_info.get('algorithm')}")
        print(f"  Salt: {encryption_info.get('salt')} (长度: {len(encryption_info.get('salt', b''))})")
        print(f"  IV/Nonce: {encryption_info.get('iv_nonce')} (长度: {len(encryption_info.get('iv_nonce', b''))})")
        
        # 步骤3: 获取加密数据
        print("\n[步骤3] 获取加密数据...")
        encrypted_data = encrypted_file.extract_encrypted_section()
        print(f"✓ 加密数据大小: {len(encrypted_data)}")
        
        # 步骤4: 创建解密器
        print("\n[步骤4] 创建解密器...")
        decryptor = Decryptor()
        print(f"✓ 解密器初始化完成 (算法: {decryptor.algorithm})")
        
        # 步骤5: 解密流
        print("\n[步骤5] 解密数据流...")
        try:
            decrypted_data = decryptor.decrypt_stream(encrypted_data, password, encryption_info)
            print(f"✓ 解密成功!")
            print(f"  解密后数据大小: {len(decrypted_data)}")
            
            # 步骤6: 保存到临时文件
            print("\n[步骤6] 保存到临时文件...")
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_file.write(decrypted_data)
            temp_file.close()
            print(f"✓ 临时文件已创建: {temp_file.name}")
            print(f"  文件大小: {os.path.getsize(temp_file.name)}")
            
            return temp_file.name
            
        except Exception as e:
            print(f"✗ 解密失败: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python test_decrypt.py <加密文件路径> <密码>")
        sys.exit(1)
    
    test_decrypt(sys.argv[1], sys.argv[2])
