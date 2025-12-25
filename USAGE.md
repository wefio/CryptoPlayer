# Shell Video Player 使用说明

Shell Video Player 是一个"壳加密视频播放器"，它将版权提示视频与加密的正片视频合并成一个文件，只有使用特定播放器才能播放完整内容。本项目支持命令行操作和图形界面操作。

## 安装依赖

在使用之前，请确保安装了必要的依赖：

```bash
pip install pycryptodome
```

或者运行项目根目录的安装脚本：

```bash
# Windows
install_deps.bat

# Linux/Mac
pip install -r requirements.txt  # 如果存在requirements.txt
```

## 功能说明

### 1. 命令行播放

播放加密视频：

```bash
python scripts/play_video.py <加密视频文件路径>

# 示例
python scripts/play_video.py encrypted_output/lesson01.enc.mp4
```

### 2. 简易加密工具

加密单个视频文件：

```bash
python simple_encrypt.py file <输入视频> <输出加密文件> -p "密码"

# 示例
python simple_encrypt.py file input.mp4 output.enc.mp4 -p "your_password"
```

批量加密文件夹中的视频：

```bash
# 加密 input_plain 文件夹中的所有mp4文件
python simple_encrypt.py folder input_plain encrypted_output

# 使用指定密码
python simple_encrypt.py folder input_plain encrypted_output -p "my_password"

# 递归处理子文件夹
python simple_encrypt.py folder input_plain encrypted_output -p "my_password" -r
```

### 3. 批量加密脚本

```bash
# 加密 input_plain 文件夹中的所有mp4文件
python batch_encrypt.py input_plain encrypted_output

# 使用指定密码
python batch_encrypt.py input_plain encrypted_output -p "my_password"

# 递归处理子文件夹
python batch_encrypt.py input_plain encrypted_output -p "my_password" -r

# 使用自定义提示视频和元数据配置
python batch_encrypt.py input_plain encrypted_output -p "my_password" -n notice_assets/notice.mp4 -m metadata.txt
```

### 4. 批量解密播放

播放文件夹中的加密视频（带批量处理功能）：

```bash
# 播放 encrypted_output 文件夹中的所有加密视频
python batch_decrypt_play.py encrypted_output -p "密码"

# 播放特定模式的加密视频文件
python batch_decrypt_play.py encrypted_output --pattern "*.enc.mp4" -p "密码"

# 递归播放子文件夹中的视频
python batch_decrypt_play.py encrypted_output -p "密码" -r

# 播放列表模式（连续播放）
python batch_decrypt_play.py encrypted_output -p "密码" --playlist
```

**注意**: `batch_decrypt_play.py` 是设计用来处理整个文件夹的，而不是单个文件。要播放单个加密视频文件，请使用 `scripts/play_video.py`。

## 文件格式说明

- **明文提示段**: 使用 FFmpeg 生成的标准 mp4，包含版权/购买提示
- **自定义文件头**: 包含加密信息的头部数据
- **AES 加密的视频流数据**: 经过加密的正片内容

## 配置文件

项目根目录下的 [config.json](file:///c:/Downloads/shellvideoplayer/config.json) 文件包含各种配置选项，如：
- FFmpeg 路径设置
- 加密算法配置
- 元数据字段白名单
- 播放器行为配置

## 注意事项

1. **密码安全**: 本项目仅为教学演示，不提供企业级安全保护
2. **FFmpeg 依赖**: 确保系统中已安装 FFmpeg 并添加到 PATH 环境变量
3. **文件格式**: 加密后的文件使用 `.enc.mp4` 扩展名
4. **系统托盘**: 托盘功能需要 PyQt5 或 PyQt6 支持

## 常见问题

Q: 播放时提示密码错误怎么办？
A: 请确认输入的密码与加密时使用的密码完全一致。

Q: 普通播放器能播放加密文件吗？
A: 可以播放文件的前半部分（版权提示内容），但无法播放加密的正片内容。

Q: 如何自定义版权提示视频？
A: 使用 `-n` 参数指定自定义提示视频文件路径。

Q: simple_encrypt.py 命令行格式是什么？
A: 该脚本使用子命令格式，需要指定 'file' 或 'folder' 子命令。

Q: batch_decrypt_play.py 如何播放单个文件？
A: `batch_decrypt_play.py` 是设计用来处理整个文件夹的，要播放单个加密视频文件，请使用 `scripts/play_video.py`。