# 批量加解密脚本使用说明

## 快速开始

### 1. 批量加密文件夹内的所有视频

```bash
# 加密 input_plain 文件夹中的所有mp4文件（带提示段）
python batch_encrypt.py input_plain encrypted_output

# 使用指定密码
python batch_encrypt.py input_plain encrypted_output -p "my_password"

# 递归处理子文件夹
python batch_encrypt.py input_plain encrypted_output -p "my_password" -r

# 使用自定义提示视频和元数据配置
python batch_encrypt.py input_plain encrypted_output -p "my_password" -n notice_assets/notice.mp4 -m metadata.txt

# 纯加密模式（无提示段）
python batch_encrypt.py input_plain encrypted_output -p "my_password" --pure-encrypt

# 试运行（不实际加密）
python batch_encrypt.py input_plain encrypted_output --dry-run

# 使用队列文件夹（自动检测queue子文件夹）
python batch_encrypt.py input_plain encrypted_output -p "my_password"

# 禁用队列文件夹功能
python batch_encrypt.py input_plain encrypted_output -p "my_password" --no-queue
```

### 2. 批量解密播放加密视频

```bash
# 播放 encrypted_output 文件夹中的所有加密视频
python batch_decrypt_play.py encrypted_output

# 使用指定密码
python batch_decrypt_play.py encrypted_output -p "my_password"

# 跳过所有提示段
python batch_decrypt_play.py encrypted_output -p "my_password" --skip-notice

# 播放列表模式（连续播放）
python batch_decrypt_play.py encrypted_output -p "my_password" --playlist

# 随机播放
python batch_decrypt_play.py encrypted_output -p "my_password" --shuffle

# 递归处理子文件夹
python batch_decrypt_play.py encrypted_output -p "my_password" -r
```

## 队列文件夹功能

### 工作原理

`input_plain` 文件夹下可以创建一个 `queue` 子文件夹。批量加密时会自动检测：

- **存在 queue 文件夹**：只处理 `input_plain/queue` 中的文件（批量处理模式）
- **不存在 queue 文件夹**：处理 `input_plain` 中的所有文件（单文件处理模式）

### 使用场景

1. **批量处理模式**：将需要批量加密的视频放入 `input_plain/queue/`，然后运行：
   ```bash
   python batch_encrypt.py input_plain encrypted_output -p "password"
   ```

2. **单文件处理模式**：直接在 `input_plain/` 中放置单个视频，运行相同命令即可：
   ```bash
   python batch_encrypt.py input_plain encrypted_output -p "password"
   ```

3. **禁用队列功能**：使用 `--no-queue` 参数强制禁用队列检测：
   ```bash
   python batch_encrypt.py input_plain encrypted_output -p "password" --no-queue
   ```

### 文件夹结构示例

```
input_plain/
├── queue/              # 批量处理：放入需要批量加密的视频
│   ├── video1.mp4
│   ├── video2.mp4
│   └── video3.mp4
└── single_video.mp4    # 单文件处理：直接加密此文件
```

## 通用文件加密工具

### 功能说明

`simple_encrypt_file.py` 支持加密任意文件类型（zip、txt、图片等），实现文件隐写术。

### 加密文件

```bash
# 纯加密模式（生成 .enc.mp4 文件）
python simple_encrypt_file.py encrypt input.zip encrypted_output.enc.mp4 -p "password"

# 使用载体视频（隐写术，加密文件伪装成视频）
python simple_encrypt_file.py encrypt input.txt secret.mp4 -p "password" -c carrier.mp4

# 指定加密算法
python simple_encrypt_file.py encrypt input.docx output.enc.mp4 -p "password" -a AES-CBC

# 使用 ChaCha20 算法
python simple_encrypt_file.py encrypt data.json output.enc.mp4 -p "password" -a ChaCha20
```

### 解密文件

```bash
# 解密文件
python simple_encrypt_file.py decrypt secret.mp4 output.txt -p "password"

# 解密纯加密文件
python simple_encrypt_file.py decrypt encrypted_output.enc.mp4 restored.zip -p "password"
```

## 通用文件解密工具

### 功能说明

`simple_decrypt_file.py` 和 `batch_decrypt_save.py` 支持将加密文件解密并保存到指定位置。

### 单文件解密

```bash
# 解密加密文件
python simple_decrypt_file.py decrypt secret.enc.mp4 output.zip -p "password"

# 解密并保存提示段（载体视频）
python simple_decrypt_file.py decrypt secret.mp4 decrypted.mp4 -p "password" --save-notice

# 解密到指定目录（自动检测文件类型）
python simple_decrypt_file.py decrypt encrypted_output/ decrypted_output/ -p "password"

# 指定加密算法
python simple_decrypt_file.py decrypt secret.enc.mp4 output.zip -p "password" -a AES-CBC
```

### 批量解密

```bash
# 批量解密文件夹中的所有加密文件
python batch_decrypt_save.py encrypted_output/ decrypted_output/ -p "password"

# 递归处理子文件夹
python batch_decrypt_save.py encrypted_output/ decrypted_output/ -p "password" -r

# 自动检测文件类型并设置正确的扩展名
python batch_decrypt_save.py encrypted_output/ decrypted_output/ -p "password"

# 保存提示段（载体视频）
python batch_decrypt_save.py encrypted_output/ decrypted_output/ -p "password" --save-notice

# 跳过已存在的文件
python batch_decrypt_save.py encrypted_output/ decrypted_output/ -p "password" --skip-existing

# 出错时停止处理
python batch_decrypt_save.py encrypted_output/ decrypted_output/ -p "password" --stop-on-error

# 使用自定义文件匹配模式
python batch_decrypt_save.py encrypted_output/ decrypted_output/ -p "password" --pattern "*.mp4"

# 从secrets/password.txt读取密码
python batch_decrypt_save.py encrypted_output/ decrypted_output/ --use-secrets
```

### 自动文件类型检测

批量解密工具会自动检测原始文件类型，并设置正确的扩展名：

- **ZIP文件**：检测文件头 `PK\x03\x04`，自动保存为 `.zip`
- **PDF文件**：检测文件头 `%PDF`，自动保存为 `.pdf`
- **PNG图片**：检测文件头 `\x89PNG`，自动保存为 `.png`
- **JPEG图片**：检测文件头 `\xff\xd8`，自动保存为 `.jpg`
- **RAR文件**：检测文件头 `Rar!`，自动保存为 `.rar`
- **7Z文件**：检测文件头 `7z\xbc\xaf\x27\x1c`，自动保存为 `.7z`
- **MP4视频**：检测文件头，自动保存为 `.mp4`
- **其他文件**：默认保存为 `.mp4`

可以使用 `--no-detect` 参数禁用自动检测，所有文件将保存为 `.mp4` 格式。

### 支持的文件类型

- **视频文件**：.mp4, .avi, .mkv, .mov, .flv, .wmv
- **图片文件**：.jpg, .jpeg, .png, .gif, .bmp, .webp
- **文本文件**：.txt, .csv, .json, .xml, .log
- **压缩文件**：.zip, .rar, .7z, .tar, .gz
- **文档文件**：.pdf, .doc, .docx, .xls, .xlsx
- **其他文件**：任意二进制文件

### 隐写术原理

当使用 `-c` 参数指定载体视频时，加密文件会伪装成该视频：

1. 提示段 = 载体视频的完整内容
2. 加密段 = 实际加密的文件数据
3. 文件头 = 加密信息（算法、盐值、IV等）

这样，加密文件看起来就像一个普通视频，可以用任何播放器播放（只播放载体视频部分），但只有知道密码的人才能解密隐藏的真实文件。

## 命令行参数

### batch_encrypt.py 参数

| 参数 | 说明 |
|------|------|
| `input_folder` | 输入文件夹路径 |
| `output_folder` | 输出文件夹路径 |
| `-p, --password` | 加密密码 |
| `-n, --notice` | 提示视频路径（可选） |
| `-m, --metadata` | 元数据配置文件路径（可选） |
| `--pure-encrypt` | 纯加密模式（无提示段） |
| `--pattern` | 文件匹配模式（默认：*.mp4） |
| `-r, --recursive` | 递归处理子文件夹 |
| `--dry-run` | 试运行，不实际加密 |
| `--config` | 配置文件路径（默认：config.json） |
| `--confirm-password` | 要求确认密码 |
| `--use-secrets` | 从 secrets/password.txt 读取密码 |
| `--no-queue` | 禁用队列文件夹功能 |

### batch_decrypt_play.py 参数

| 参数 | 说明 |
|------|------|
| `input_folder` | 加密视频文件夹路径 |
| `-p, --password` | 解密密码 |
| `--pattern` | 文件匹配模式（默认：*.enc.mp4） |
| `-r, --recursive` | 递归处理子文件夹 |
| `--skip-notice` | 跳过所有提示段 |
| `--ask-each` | 为每个文件单独询问密码 |
| `--stop-on-error` | 出错时停止播放 |
| `--playlist` | 播放列表模式（连续播放） |
| `--shuffle` | 随机播放 |
| `--config` | 配置文件路径（默认：config.json） |
| `--use-secrets` | 从 secrets/password.txt 读取密码 |

### simple_encrypt_file.py 参数

| 参数 | 说明 |
|------|------|
| `encrypt` | 加密命令 |
| `decrypt` | 解密命令 |
| `input` | 输入文件路径 |
| `output` | 输出文件路径 |
| `-p, --password` | 加密/解密密码 |
| `-c, --carrier` | 载体视频路径（用于隐写术） |
| `-a, --algorithm` | 加密算法（AES-CTR/AES-CBC/ChaCha20） |
| `--pure` | 纯加密模式（不使用载体视频） |
