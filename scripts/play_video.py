#!/usr/bin/env python3
# scripts/play_video.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from player.core.video_processor import VideoProcessor
from player.cli.interface import CLIInterface
from player.exceptions.custom_exceptions import VideoEncryptionError, PasswordError


def main():
    """播放加密视频主函数"""
    if len(sys.argv) < 2:
        print("用法: python play_video.py <加密视频文件>")
        print("示例: python play_video.py encrypted_output/lesson01.enc.mp4")
        sys.exit(1)

    encrypted_path = sys.argv[1]

    cli = CLIInterface()
    processor = VideoProcessor()

    try:
        # 显示加密文件信息
        cli.show_video_info(encrypted_path)

        # 提示输入密码
        password = cli.prompt_for_password()

        # 询问是否跳过提示段
        skip_notice = cli.ask_skip_notice()

        # 解密并播放
        print("\n开始解密并播放视频...")
        success = processor.decrypt_and_play(
            encrypted_path=encrypted_path,
            password=password,
            skip_notice=skip_notice
        )

        if success:
            cli.show_success("视频播放完成！")
        else:
            print("播放失败")

    except PasswordError as e:
        cli.show_error(e)
        sys.exit(1)
    except VideoEncryptionError as e:
        cli.show_error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"未知错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()