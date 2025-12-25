# MCP服务器使用说明

## 概述

`mcp_server.py` 提供了一个MCP (Model Context Protocol) 服务器，允许AI助手调用视频加密播放器的所有功能。

## 可用工具

### 1. encrypt_file
加密单个文件（支持视频和任意文件类型）

**参数：**
- `input_path` (必需): 输入文件路径
- `output_path` (必需): 输出文件路径
- `password` (必需): 加密密码
- `notice_video_path` (可选): 提示视频路径（用于隐写术）
- `algorithm` (可选): 加密算法（AES-CTR/AES-CBC/ChaCha20，默认：AES-CTR）
- `pure_encrypt` (可选): 纯加密模式（无提示段，默认：false）

**示例：**
```python
{
    "input_path": "input_plain/video.mp4",
    "output_path": "encrypted_output/video.enc.mp4",
    "password": "my_password",
    "algorithm": "AES-CTR"
}
```

### 2. decrypt_file
解密加密文件

**参数：**
- `input_path` (必需): 加密文件路径
- `output_path` (必需): 输出文件路径
- `password` (必需): 解密密码
- `save_notice` (可选): 保存提示段（载体视频，默认：false）

**示例：**
```python
{
    "input_path": "encrypted_output/video.enc.mp4",
    "output_path": "decrypted_output/video.mp4",
    "password": "my_password"
}
```

### 3. play_encrypted_video
播放加密视频

**参数：**
- `encrypted_path` (必需): 加密视频文件路径
- `password` (必需): 解密密码
- `skip_notice` (可选): 跳过提示段（默认：false）

**示例：**
```python
{
    "encrypted_path": "encrypted_output/video.enc.mp4",
    "password": "my_password",
    "skip_notice": false
}
```

### 4. get_file_info
获取加密文件信息

**参数：**
- `file_path` (必需): 加密文件路径

**示例：**
```python
{
    "file_path": "encrypted_output/video.enc.mp4"
}
```

### 5. batch_encrypt
批量加密文件夹中的文件

**参数：**
- `input_folder` (必需): 输入文件夹路径
- `output_folder` (必需): 输出文件夹路径
- `password` (必需): 加密密码
- `pattern` (可选): 文件匹配模式（默认：*.mp4）
- `recursive` (可选): 递归处理子文件夹（默认：false）
- `pure_encrypt` (可选): 纯加密模式（默认：false）

**示例：**
```python
{
    "input_folder": "input_plain",
    "output_folder": "encrypted_output",
    "password": "my_password",
    "pattern": "*.mp4",
    "recursive": false
}
```

### 6. batch_decrypt
批量解密文件夹中的文件

**参数：**
- `input_folder` (必需): 加密文件文件夹路径
- `output_folder` (必需): 解密文件输出文件夹路径
- `password` (必需): 解密密码
- `pattern` (可选): 文件匹配模式（默认：*.enc.mp4）
- `recursive` (可选): 递归处理子文件夹（默认：false）
- `save_notice` (可选): 保存提示段（默认：false）

**示例：**
```python
{
    "input_folder": "encrypted_output",
    "output_folder": "decrypted_output",
    "password": "my_password",
    "pattern": "*.enc.mp4"
}
```

### 7. list_available_files
列出可用文件

**参数：**
- `folder` (可选): 文件夹类型（input_plain/encrypted_output/decrypted_output/all）

**示例：**
```python
{
    "folder": "all"
}
```

## 配置MCP服务器

### 方法1: 在Claude Desktop中配置

1. 打开Claude Desktop配置文件
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. 添加以下配置：
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

3. 重启Claude Desktop

### 方法2: 在Cline中配置

1. 打开VSCode设置 (Ctrl+,)
2. 搜索 "MCP"
3. 添加MCP服务器配置：
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

### 方法3: 在其他AI客户端中配置

参考你的AI客户端的MCP配置文档，使用以下命令：
```bash
python c:/Downloads/shellvideoplayer/mcp_server.py
```

## 测试MCP服务器

运行以下命令测试MCP服务器是否正常工作：

```bash
python mcp_server.py
```

你应该看到服务器信息和可用工具列表。

## 使用示例

### 示例1: 加密视频

向AI发送：
```
请加密 input_plain/video.mp4 文件，密码是 "my_password"，输出到 encrypted_output/video.enc.mp4
```

AI会自动调用 `encrypt_file` 工具。

### 示例2: 解密文件

向AI发送：
```
请解密 encrypted_output/video.enc.mp4 文件，密码是 "my_password"，保存到 decrypted_output/video.mp4
```

AI会自动调用 `decrypt_file` 工具。

### 示例3: 批量加密

向AI发送：
```
请批量加密 input_plain 文件夹中的所有mp4文件，密码是 "my_password"，输出到 encrypted_output 文件夹
```

AI会自动调用 `batch_encrypt` 工具。

### 示例4: 获取文件信息

向AI发送：
```
请获取 encrypted_output/video.enc.mp4 文件的信息
```

AI会自动调用 `get_file_info` 工具。

### 示例5: 列出可用文件

向AI发送：
```
请列出所有可用的文件
```

AI会自动调用 `list_available_files` 工具。

## 高级用法

### 隐写术加密

向AI发送：
```
请加密 input_plain/secret.zip 文件，使用 notice_assets/notice.mp4 作为载体视频，密码是 "my_password"
```

这将创建一个伪装成视频的加密文件。

### 纯加密模式

向AI发送：
```
请加密 input_plain/video.mp4 文件，使用纯加密模式（无提示段），密码是 "my_password"
```

### 自定义加密算法

向AI发送：
```
请使用 ChaCha20 算法加密 input_plain/video.mp4 文件，密码是 "my_password"
```

## 注意事项

1. **安全性**: 密码在传输过程中是明文的，请确保在安全的环境中使用
2. **路径**: 使用绝对路径或相对于MCP服务器的工作目录的路径
3. **权限**: 确保MCP服务器有读取输入文件和写入输出文件的权限
4. **错误处理**: 所有工具都返回 success 字段，检查该字段以确定操作是否成功

## 故障排除

### 问题: MCP服务器无法连接

**解决方案：**
1. 检查Python路径是否正确
2. 确保mcp_server.py文件路径正确
3. 重启AI客户端

### 问题: 工具调用失败

**解决方案：**
1. 检查文件路径是否正确
2. 确保文件存在
3. 检查是否有足够的磁盘空间
4. 查看错误消息获取更多信息

### 问题: 加密/解密失败

**解决方案：**
1. 检查密码是否正确
2. 确保文件格式受支持
3. 检查是否有足够的内存
4. 查看详细的错误消息

## 扩展功能

MCP服务器可以轻松扩展以添加新功能：

1. 在 `mcp_server.py` 的 `_register_tools` 方法中添加新工具定义
2. 在 `ShellVideoPlayerMCP` 类中实现新方法
3. 重启MCP服务器

## 支持

如有问题，请查看：
- 项目README.md
- BATCH_USAGE.md - 批量操作文档
- USAGE.md - 基本使用文档
