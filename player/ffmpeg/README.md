# 内置FFmpeg组件说明

## 概述

本文件夹包含内置的FFmpeg可执行文件，为Windows用户提供开箱即用的使用体验，无需手动配置环境变量。

## 文件结构

```
player/ffmpeg/
├── bin/                    # FFmpeg可执行文件（仅保留此文件夹）
│   ├── ffmpeg.exe        # FFmpeg主程序
│   ├── ffplay.exe        # FFplay播放器
│   └── ffprobe.exe        # FFprobe视频信息工具
├── ffmpeg_wrapper.py      # FFmpeg Python封装器
├── cleanup.py            # 清理脚本（已删除不必要的doc/presets文件夹）
├── LICENSE               # GPL许可证
└── README.txt            # 此文档
```

## 功能

### 1. 自动路径检测

`ffmpeg_wrapper.py` 会自动检测FFmpeg路径，优先级如下：

1. **用户提供的路径** - 如果在初始化时指定
2. **内置FFmpeg** - 自动使用 `player/ffmpeg/bin/ffmpeg.exe`
3. **系统PATH** - 最后尝试使用系统命令 `ffmpeg`

示例：
```python
from player.ffmpeg.ffmpeg_wrapper import FFmpegWrapper

# 自动使用内置FFmpeg
ffmpeg = FFmpegWrapper()

# 使用系统PATH中的FFmpeg（如果需要）
ffmpeg = FFmpegWrapper(ffmpeg_path="ffmpeg")
```

### 2. 跨平台编码处理

自动检测操作系统并使用正确的编码：
- **Windows**: 使用 `gbk` 编码处理FFmpeg输出
- **Linux/macOS**: 使用 `utf-8` 编码

### 3. 主要功能

#### extract_video_stream()
提取视频裸流（包含音频），不重新编码。

```python
ffmpeg = FFmpegWrapper()
ffmpeg.extract_video_stream("input.mp4", "output.mp4", codec="copy")
```

#### generate_notice_video()
生成提示视频（用于加密提示段）。

```python
ffmpeg = FFmpegWrapper()
ffmpeg.generate_notice_video(
    assets={'text': '请购买完整版本'},
    output_path="notice.mp4",
    duration=10
)
```

#### play_video()
播放视频，支持自动缩放适应屏幕。

```python
ffmpeg = FFmpegWrapper()
ffmpeg.play_video("video.mp4", title="播放标题")
```

#### get_video_info()
获取视频详细信息（分辨率、编解码器、时长等）。

```python
ffmpeg = FFmpegWrapper()
info = ffmpeg.get_video_info("video.mp4")
print(info)
```

#### add_metadata()
为视频添加元数据。

```python
ffmpeg = FFmpegWrapper()
ffmpeg.add_metadata("input.mp4", "output.mp4", {
    'title': '视频标题',
    'comment': '备注信息'
})
```

#### concat_files()
拼接多个视频文件。

```python
ffmpeg = FFmpegWrapper()
ffmpeg.concat_files(["video1.mp4", "video2.mp4"], "output.mp4")
```

## 使用示例

### 在项目中使用

```python
from player.core.video_processor import VideoProcessor
from player.ffmpeg.ffmpeg_wrapper import FFmpegWrapper

# 创建FFmpeg封装器（自动使用内置FFmpeg）
ffmpeg = FFmpegWrapper()

# 提取视频流
ffmpeg.extract_video_stream("input.mp4", "output.mp4")

# 生成提示视频
ffmpeg.generate_notice_video(
    assets={'text': '这是提示文本'},
    output_path="notice.mp4",
    duration=10
)

# 播放视频
ffmpeg.play_video("video.mp4")

# 获取视频信息
info = ffmpeg.get_video_info("video.mp4")
print(f"分辨率: {info.get('streams', [{}])[0].get('width', 'N/A')}x{info.get('streams', [{}])[0].get('height', 'N/A')}")
```

### 系统PATH中的FFmpeg

如果你已经在系统PATH中安装了FFmpeg，仍然可以继续使用。`ffmpeg_wrapper.py` 会自动检测并使用系统版本。

要切换回系统版本：
```python
ffmpeg = FFmpegWrapper(ffmpeg_path="ffmpeg")
```

## 常见问题

### Q: 如何使用不同版本的FFmpeg？
A: 将新的可执行文件放入 `player/ffmpeg/bin/` 目录即可。

### Q: 可以同时使用内置和系统FFmpeg吗？
A: 可以。在初始化时指定 `ffmpeg_path="ffmpeg"` 来使用系统版本。

### Q: 如何验证FFmpeg是否可用？
A: `ffmpeg_wrapper.py` 会在初始化时自动验证，如果不可用会抛出 `FFmpegError` 异常。

### Q: Linux/macOS用户怎么用？
A: 内置FFmpeg仅适用于Windows。Linux/macOS用户应该：
1. 使用系统包管理器安装FFmpeg（`sudo apt install ffmpeg`）
2. 确保FFmpeg在PATH中
3. `ffmpeg_wrapper.py` 会自动检测并使用系统版本

### Q: 清理脚本删除了什么？
A: 清理脚本删除了：
- `doc/` 文件夹（FFmpeg文档）
- `presets/` 文件夹（编码预设）

保留了：
- `bin/` 文件夹（ffmpeg.exe, ffplay.exe, ffprobe.exe）
- `ffmpeg_wrapper.py`（Python封装器）
- `LICENSE` 和 `README.txt`

## 故障排除

### FFmpeg不可用
```
FFmpegError: FFmpeg不可用，请确保 player/ffmpeg/bin/ffmpeg.exe 在PATH中
```

**解决方案**: 确认 `player/ffmpeg/bin/ffmpeg.exe` 文件存在。

### Windows编码错误
如果遇到编码错误，确保：
1. 你的控制台使用的是UTF-8编码
2. 文件路径不包含特殊字符

### 文件路径问题
Windows路径建议使用原始字符串或双反斜杠：
```python
ffmpeg.extract_video_stream(r"input.mp4", r"output.mp4")
# 或
ffmpeg.extract_video_stream("input\\path\\input.mp4", "output\\path\\output.mp4")
```

## 许可证

内置FFmpeg组件遵循GPL许可证（详见LICENSE文件）。

## 更新和维护

### 更新FFmpeg版本
1. 下载新的FFmpeg构建（建议使用static build）
2. 将 `ffmpeg.exe`, `ffplay.exe`, `ffprobe.exe` 复制到 `player/ffmpeg/bin/` 目录
3. 保留旧的 `LICENSE` 文件

### 重新清理
如果需要重新清理（例如恢复doc文件夹），运行：
```bash
cd player/ffmpeg
python cleanup.py
```

## 技术支持

如遇问题，请检查：
1. FFmpeg版本兼容性
2. Windows系统权限
3. Python版本（推荐3.7+）
