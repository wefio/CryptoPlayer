#!/usr/bin/env python3
# scripts/encrypt_video.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from player.core.video_processor import VideoProcessor
from player.cli.interface import CLIInterface
from player.exceptions.custom_exceptions import VideoEncryptionError


def main():
    """加密视频主函数"""
    if len(sys.argv) < 3:
        print("用法: python encrypt_video.py <输入视频> <输出文件>")
        print("示例: python encrypt_video.py input_plain/lesson01.mp4 encrypted_output/lesson01.enc.mp4")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    cli = CLIInterface()
    processor = VideoProcessor()

    try:
        # 显示输入视频信息
        cli.show_video_info(input_path)

        # 提示输入密码
        password = cli.prompt_for_password(confirm=True)

        # 询问是否使用自定义提示视频
        use_custom_notice = input("使用自定义提示视频？(y/n, 默认n): ").strip().lower() == 'y'
        notice_video_path = None
        if use_custom_notice:
            notice_video_path = input("请输入提示视频路径: ").strip()

        # 询问是否使用元数据配置
        use_metadata = input("使用元数据配置？(y/n, 默认n): ").strip().lower() == 'y'
        metadata_config = None
        if use_metadata:
            metadata_config = input("请输入元数据配置文件路径: ").strip()
            if not os.path.exists(metadata_config):
                print(f"警告: 元数据配置文件不存在，将不使用元数据")

        # 执行加密
        print("\n开始加密视频...")
        success = processor.encrypt_video(
            input_path=input_path,
            output_path=output_path,
            password=password,
            notice_video_path=notice_video_path,
            metadata_config=metadata_config
        )

        if success:
            cli.show_success("视频加密完成！")
            cli.show_video_info(output_path)
        else:
            print("加密失败")

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