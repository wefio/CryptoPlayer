# Shell Video Player - AI助手使用指南

## 项目概述

这是一个"壳加密视频播放器"项目，将版权提示视频与加密的正片视频合并成一个文件。只有使用特定播放器才能播放完整内容。

**核心概念**：
- **提示段**：版权/购买提示视频（前10秒左右），任何播放器都可以播放
- **加密段**：使用AES加密的实际视频内容，只有本程序可以解密播放
- **文件格式**：合并为一个MP4文件，普通播放器只看到提示段

## 核心功能

### 1. 加密功能
- **视频加密**：加密视频文件，可选择提示视频
- **通用文件加密**：支持任意文件类型（zip、txt、图片等）
- **隐写术模式**：使用载体视频隐藏加密文件，伪装成普通视频
- **批量加密**：批量处理文件夹中的文件
- **队列文件夹**：`input_plain/queue/` 自动检测

### 2. 解密功能
- **解密播放**：解密并播放加密视频
- **解密保存**：解密并保存到指定位置
- **批量解密**：批量解密文件夹中的文件
- **自动文件类型检测**：ZIP、PDF、PNG、JPEG、RAR、7Z、MP4等

### 3. 播放功能
- **FFmpeg播放**：使用内置FFmpeg播放视频
- **自动屏幕适配**：高分辨率视频自动缩放以适应屏幕
- **提示段控制**：可选择跳过或播放提示段

### 4. 密码管理
- **密码文件**：`secrets/password.txt` 存储密码
- **密码输入**：支持手动输入和从文件读取

## AI调用方式（通过MCP）

项目提供MCP服务器，AI助手可以通过以下工具调用功能：

### 工具列表

#### 1. encrypt_file
加密单个文件（支持视频和任意文件类型）

```json
{
  "input_path": "input_plain/video.mp4",
  "output_path": "encrypted_output/video.enc.mp4",
  "password": "my_password",
  "algorithm": "AES-CTR",
  "notice_video_path": "notice_assets/notice.mp4",
  "pure_encrypt": false
}
```

#### 2. decrypt_file
解密加密文件并保存

```json
{
  "input_path": "encrypted_output/video.enc.mp4",
  "output_path": "decrypted_output/video.mp4",
  "password": "my_password",
  "save_notice": false
}
```

#### 3. play_encrypted_video
播放加密视频

```json
{
  "encrypted_path": "encrypted_output/video.enc.mp4",
  "password": "my_password",
  "skip_notice": false
}
```

#### 4. get_file_info
获取加密文件信息

```json
{
  "file_path": "encrypted_output/video.enc.mp4"
}
```

#### 5. batch_encrypt
批量加密文件夹中的文件

```json
{
  "input_folder": "input_plain",
  "output_folder": "encrypted_output",
  "password": "my_password",
  "pattern": "*.mp4",
  "recursive": false,
  "pure_encrypt": false
}
```

#### 6. batch_decrypt
批量解密文件夹中的文件

```json
{
  "input_folder": "encrypted_output",
  "output_folder": "decrypted_output",
  "password": "my_password",
  "pattern": "*.enc.mp4",
  "recursive": false,
  "save_notice": false
}
```

#### 7. list_available_files
列出可用文件

```json
{
  "folder": "all"
}
```

## 文件结构

```
shellvideoplayer/
├── mcp_server.py              # MCP服务器（AI调用入口）
├── interactive_tool.py         # 交互式命令行工具
├── batch_encrypt.py            # 批量加密脚本
├── batch_decrypt_play.py        # 批量解密播放脚本
├── batch_decrypt_save.py        # 批量解密保存脚本
├── simple_encrypt_file.py        # 通用文件加密工具
├── simple_decrypt_file.py        # 通用文件解密工具
│
├── input_plain/               # 待加密的原始文件
│   ├── queue/                 # 队列文件夹（批量处理）
│   ├── video.mp4
│   └── document.zip
│
├── encrypted_output/          # 加密后的输出文件
│   ├── video.enc.mp4
│   └── document.enc.mp4
│
├── decrypted_output/          # 解密后的文件
│   ├── video.mp4
│   └── document.zip
│
├── notice_assets/             # 提示视频资源
│   ├── Never_Gonna_Give_You_Up.mp4
│   └── notice.txt
│
├── secrets/                   # 密码文件
│   └── password.txt
│
└── player/                    # 核心模块
    ├── core/                   # 核心加解密功能
    │   ├── encryptor.py        # 加密器
    │   ├── decryptor.py        # 解密器
    │   └── video_processor.py  # 视频处理器
    ├── crypto/                 # 加密算法
    │   ├── base_encryptor.py  # 基础加密器接口
    │   ├── aes_encryptor.py    # AES加密实现
    │   └── chacha20_encryptor.py # ChaCha20加密实现
    ├── file/                   # 文件处理
    │   ├── file_header.py      # 文件头定义
    │   └── encrypted_video.py # 加密视频文件格式
    └── ffmpeg/                 # FFmpeg封装
        ├── bin/                # 内置FFmpeg可执行文件（Windows）
        │   ├── ffmpeg.exe
        │   ├── ffplay.exe
        │   └── ffprobe.exe
        └── ffmpeg_wrapper.py  # FFmpeg Python封装器
```

## AI使用场景

### 场景1：加密视频文件

用户请求：请加密这个视频

AI应执行：
1. 使用 `list_available_files` 列出 `input_plain` 中的文件
2. 使用 `encrypt_file` 加密选中的视频

示例对话：
```
User: 请加密 input_plain/video.mp4
AI: 我先查看可用的文件...
[使用 list_available_files tool]

AI: 现在开始加密 video.mp4...
[使用 encrypt_file tool: {
  "input_path": "input_plain/video.mp4",
  "output_path": "encrypted_output/video.enc.mp4",
  "password": "secure_password_123"
}]
```

### 场景2：解密并播放视频

用户请求：播放这个加密视频

AI应执行：
1. 使用 `play_encrypted_video` 播放视频
2. 如果需要密码，询问用户

示例对话：
```
User: 播放 encrypted_output/video.enc.mp4
AI: 我需要密码才能解密播放。请提供密码。
User: 密码是 secure_password_123
AI: 好的，现在开始播放...
[使用 play_encrypted_video tool]
```

### 场景3：加密非视频文件（隐写术）

用户请求：把这个zip文件隐藏到视频里

AI应执行：
1. 使用 `encrypt_file` 加密zip文件，指定载体视频

示例对话：
```
User: 我需要把 confidential.zip 隐藏到一个视频里
AI: 我可以帮你创建一个隐写文件。我将使用载体视频来隐藏zip文件。
[使用 encrypt_file tool: {
  "input_path": "input_plain/confidential.zip",
  "output_path": "encrypted_output/secret.mp4",
  "password": "hidden_password_456",
  "notice_video_path": "notice_assets/notice.mp4"
}]
```

### 场景4：批量处理文件夹

用户请求：加密这个文件夹里的所有视频

AI应执行：
1. 使用 `batch_encrypt` 批量加密

示例对话：
```
User: 请加密 input_plain 文件夹里的所有mp4文件
AI: 我将开始批量加密...
[使用 batch_encrypt tool: {
  "input_folder": "input_plain",
  "output_folder": "encrypted_output",
  "password": "batch_password_789",
  "pattern": "*.mp4"
}]
```

### 场景5：解密保存文件

用户请求：解密这个文件并保存

AI应执行：
1. 使用 `decrypt_file` 解密并保存

示例对话：
```
User: 解密 encrypted_output/document.enc.mp4 保存为zip文件
AI: 好的，我现在开始解密...
[使用 decrypt_file tool: {
  "input_path": "encrypted_output/document.enc.mp4",
  "output_path": "decrypted_output/document.zip",
  "password": "hidden_password_456"
}]
```

## 重要注意事项

### 1. 隐写文件检测

当文件名包含 `zip`、`rar`、`7z`、`pdf`、`doc`、`txt`、`image`、`portable` 等关键词时，这可能是隐写文件。使用 `decrypt_file` 解密而不是 `play_encrypted_video`。

### 2. 密码安全

- ⚠️ 不要在对话中明文显示密码
- ⚠️ 建议用户设置密码后再操作
- ⚠️ `secrets/password.txt` 仅用于开发测试

### 3. 文件路径

- Windows路径使用原始字符串或双反斜杠：`r"path\to\file"`
- 相对路径基于项目根目录

### 4. 加密算法

支持3种加密算法：
- **AES-CTR**：推荐，速度快，适合视频
- **AES-CBC**：更安全的模式，但略慢
- **ChaCha20**：高性能流密码

### 5. 文件类型检测

批量解密时会自动检测文件类型并设置正确扩展名：
- ZIP文件 → `.zip`
- PDF文件 → `.pdf`
- PNG/JPEG图片 → `.png`/`.jpg`
- MP4视频 → `.mp4`

### 6. 错误处理

所有工具都返回 `success` 字段：
- `true`: 操作成功
- `false`: 操作失败，检查 `error` 字段获取详细信息

## MCP配置

### Claude Desktop配置

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "shell-video-player": {
      "command": "python",
      "args": [
        "c:/Downloads/shellvideoplayer/mcp_server.py"
      ]
    }
  }
}
```

### 使用方法

1. AI助手会自动检测可用的工具
2. 用户可以用自然语言描述需求
3. AI调用相应的MCP工具
4. AI根据工具返回的结果进行反馈

## 完整工作流示例

### 加密-解密完整流程

```
1. 用户: 我有一个视频 video.mp4，想加密它
   AI: [使用 encrypt_file] 
   AI: ✓ 加密成功！文件已保存到 encrypted_output/video.enc.mp4

2. 用户: 现在播放它
   AI: [使用 play_encrypted_video]
   AI: ✓ 播放完成！

3. 用户: 我需要修改视频，帮我解密
   AI: [使用 decrypt_file 解密到 input_plain/video_back.mp4]
   AI: ✓ 解密成功！文件已保存
```

### 隐写术流程

```
1. 用户: 把这个 confidential.zip 隐藏到一个视频里
   AI: [使用 encrypt_file，指定载体视频]
   AI: ✓ 隐写成功！输出文件 encrypted_output/secret.mp4

2. 用户: 我怎么获取zip文件？
   AI: [使用 decrypt_file 解密到 decrypted_output/confidential.zip]
   AI: ✓ 解密成功！原文件已恢复
```

## 故障排除

### 问题：FFmpeg不可用

**错误信息**：`FFmpeg不可用，请确保 player/ffmpeg/bin/ffmpeg.exe 在PATH中`

**解决方案**：
1. 检查 `player/ffmpeg/bin/ffmpeg.exe` 是否存在
2. 如果不存在，内置FFmpeg未正确安装
3. 系统PATH中的FFmpeg也可以使用

### 问题：密码错误

**错误信息**：`解密失败: [Crypto] 解密失败`

**解决方案**：
1. 确认密码正确
2. 检查加密算法是否匹配
3. 确认文件没有损坏

### 问题：文件格式错误

**错误信息**：`获取视频信息失败`

**解决方案**：
1. 确认文件是有效的MP4格式
2. 尝试重新生成文件
3. 检查FFmpeg版本兼容性

## 扩展功能

### 1. 交互式工具

提供完整的命令行交互界面：

```bash
python interactive_tool.py
```

菜单选项：
- [1] 加密视频
- [2] 解密播放
- [3] 解密保存
- [4] 设置密码
- [5] 退出

### 2. 命令行脚本

```bash
# 批量加密
python batch_encrypt.py input_plain encrypted_output -p "password"

# 批量解密播放
python batch_decrypt_play.py encrypted_output -p "password"

# 批量解密保存
python batch_decrypt_save.py encrypted_output decrypted_output -p "password"

# 通用文件加密
python simple_encrypt_file.py encrypt input.zip output.zip -p "password"

# 通用文件解密
python simple_decrypt_file.py decrypt input.zip output.zip -p "password"
```

### 3. 内置FFmpeg

Windows用户自动使用内置FFmpeg：
- 自动检测：`player/ffmpeg/bin/ffmpeg.exe`
- 可以手动指定：`FFmpegWrapper(ffmpeg_path="custom_ffmpeg")`
- 系统FFmpeg：`FFmpegWrapper(ffmpeg_path="ffmpeg")`

## 安全建议

### 开发环境
- ⚠️ `secrets/password.txt` 仅用于测试
- ✅ 生产环境使用环境变量或密钥管理系统
- ✅ 不要提交密码文件到版本控制

### 生产环境
- ✅ 使用强密码（16位以上）
- ✅ 定期更换密码
- ✅ 使用环境变量管理敏感信息
- ✅ 启用文件加密和访问控制

## 总结

这是一个功能完整的视频加密播放器，支持：

✅ **视频加密**：使用AES/AES-CBC/ChaCha20算法
✅ **通用文件加密**：支持任意文件类型
✅ **隐写术模式**：使用载体视频隐藏加密文件
✅ **批量处理**：支持批量加密/解密
✅ **解密播放**：内置FFmpeg播放器
✅ **解密保存**：解密并保存到指定位置
✅ **MCP支持**：AI可以通过MCP调用所有功能
✅ **内置FFmpeg**：Windows用户开箱即用
✅ **自动文件类型检测**：智能识别文件类型
✅ **交互式工具**：友好的命令行界面

**适用场景**：
- 教学/Demo项目
- 内容保护
- 视频版权保护
- 文件隐写术
- 批量视频处理
