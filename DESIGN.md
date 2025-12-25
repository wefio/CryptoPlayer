# FFmpeg 壳加密视频播放器 Demo 设计文档

## 1. 项目背景与目标

本项目是一个**教学 / Demo 性质的加密视频播放器设计**，用于理解并演示：

- 视频流级加密的基本原理
- "壳文件 + 指定播放器" 的工程实现方式
- 如何在**不对抗标准播放器**的前提下，提供版权与购买提示

⚠️ 本项目**仅用于处理用户自己拥有版权的视频内容**，不涉及也不鼓励任何 DRM 绕过行为。

### 1.1 设计目标

- 使用 FFmpeg 作为底层播放与解码工具
- 不依赖 GUI，可通过命令行完成主要交互
- 普通播放器可播放“版权提示内容”
- 加密后的正片只能通过本 Demo 播放
- 项目结构清晰，便于理解和二次开发

---

## 2. 整体架构概览

### 2.1 系统组件

```
┌────────────┐
│ 原始视频   │
└─────┬──────┘
      │
      ▼
┌────────────┐        ┌──────────────────┐
│ 加密工具   │──────▶│ 壳加密视频文件   │
└────────────┘        └────────┬─────────┘
                                 │
                 普通播放器     │     Demo 播放器
               （仅播提示）     │   （完整解密播放）
                                 ▼
                           FFmpeg 解码播放
```

---

## 3. 文件与目录结构设计

```
project_root/
│
├─ input_plain/          # 待加密的原始视频（用户自有版权）
│   └─ lesson01.mp4
│
├─ notice_assets/        # 版权/购买提示资源（明文）
│   ├─ notice.png
│   ├─ notice.mp4
│   └─ notice.txt
│
├─ encrypted_output/     # 加密后的输出文件
│   └─ lesson01.enc.mp4
│
├─ secrets/
│   └─ password.txt      # 加密密码（Demo 使用，非安全存储）
│
├─ player/               # 播放器程序本体
│   ├─ encrypt.py        # 加密工具
│   ├─ decrypt_play.py   # 解密 + 播放
│   └─ README.md
│
└─ DESIGN.md             # 本设计文档
```

---

## 4. 加密文件格式设计（Demo 级）

### 4.1 文件逻辑结构

```
[ 明文提示段 (notice.mp4) ]
[ 自定义文件头 ]
[ AES 加密的视频流数据 ]
```

### 4.2 明文提示段

- 使用 FFmpeg 生成的标准 mp4
- 内容：
  - 版权声明
  - 购买方式
  - 官方播放器说明
- 普通播放器可完整播放此部分

### 4.3 自定义文件头（简化）

| 字段 | 长度 | 说明 |
|----|----|----|
| MAGIC | 4B | 固定标识，如 `ENCV` |
| VERSION | 1B | 格式版本 |
| NOTICE_LEN | 4B | 提示段长度 |
| RESERVED | nB | 预留 |

播放器通过该头信息定位加密数据起点。

---

## 5. 媒体信息（Metadata）设计

### 5.1 设计目的

为了增强文件的**可解释性、可玩性与工程完整度**，本 Demo 支持通过**独立文本文件**定义并注入媒体信息（Metadata），使得：

- MediaInfo / ffprobe 可直接读取说明信息
- 普通播放器与技术用户都能获得清晰提示
- 信息注入逻辑与视频内容解耦，便于维护

该设计属于**标准容器规范允许范围内的信息利用**，不构成任何规避或对抗行为。

---

### 5.2 Metadata 配置文件

在项目根目录下新增配置文件：

```
metadata.txt
```

该文件用于描述希望写入视频容器的媒体信息。

#### 5.2.1 基本格式（Key=Value）

```text
title=加密课程示例
artist=Your Name
comment=本文件包含加密内容，仅官方播放器可完整播放
copyright=© 2025 Your Name
encoder=Encrypted Demo Player / FFmpeg
description=购买地址：https://example.com
```

- 每行一个字段
- 空行与 `#` 开头的行视为注释
- Key 对应 FFmpeg 支持的 metadata 字段

---

### 5.3 覆盖与追加策略

Metadata 写入支持两种模式：

#### 5.3.1 覆盖模式（默认）

- `metadata.txt` 中出现的字段
- **直接覆盖**原有同名字段

适用于：
- 明确指定版权与说明信息
- Demo / 教学场景

#### 5.3.2 追加模式（可选）

- 若字段已存在
- 新内容以 `; ` 或换行方式追加

示例：

```text
comment+=本视频为教学 Demo;
comment+=完整内容需使用官方播放器
```

播放器或打包脚本需解析 `+=` 语义。

---

### 5.4 写入位置与层级

Metadata 可写入以下位置：

| 层级 | 位置 | 用途 |
|----|----|----|
| 播放层 | notice.mp4 | 普通用户可见 |
| 容器层 | MP4 standard metadata | MediaInfo / ffprobe |
| 用户层 | udta / user data box | 结构化信息（JSON） |

本 Demo **至少实现容器层写入**，其余为可扩展项。

---

### 5.5 与加密流程的关系

Metadata 注入发生在：

1. notice.mp4 生成完成后
2. 加密正片拼接之前

保证：
- 普通播放器可读
- 加密流程不影响 metadata

---

## 6. 加密流程设计

### 5.1 输入

- 原始视频：`input_plain/*.mp4`
- 密码：`secrets/password.txt`

### 5.2 处理步骤

1. 使用 FFmpeg 拆分原始视频为裸流
2. 使用 AES（CTR 或 CBC）对视频流加密
3. 生成或读取 `notice.mp4`
4. 按格式拼接生成最终文件

### 5.3 密码使用说明（Demo 级）

- 密码仅用于派生 AES key
- 不涉及授权服务器
- 不防止暴力破解（教学目的）

---

## 6. 播放器设计（无 GUI）

### 6.1 使用方式

```bash
python decrypt_play.py encrypted_output/lesson01.enc.mp4
```

### 6.2 播放流程

1. 读取文件头
2. 播放明文提示段（可选跳过）
3. 校验密码
4. 解密视频流到内存 / 管道
5. 通过 FFmpeg / ffplay 播放

### 6.3 交互设计（CLI）

- 启动时提示：
  - 视频名称
  - 是否播放提示段
- 密码错误提示
- 解密失败提示

---

## 7. 依赖与环境

- FFmpeg（命令行）
- Python 3.9+
- pycryptodome

---

## 8. 安全与限制说明

- 本项目不提供：
  - DRM 强度保证
  - 防录屏、防内存抓取
- 明确定位为：
  - 教学 Demo
  - 工程理解示例

---

## 8. Metadata 字段白名单与规范

### 8.1 设计原则

为了避免 Metadata 被滥用或变得不可维护，本 Demo 明确区分：

- **推荐字段（白名单）**：稳定、通用、建议使用
- **扩展字段**：用于实验或彩蛋
- **结构字段**：供播放器或工具解析

---

### 8.2 Metadata 字段白名单表（容器层）

| 字段名 | 用途 | MediaInfo 可见 | 备注 |
|----|----|----|----|
| title | 视频标题 | 是 | 推荐 |
| artist | 作者 / 机构 | 是 | 推荐 |
| comment | 简要说明 | 是 | 推荐，支持追加 |
| description | 详细说明 | 是 | 可放购买链接 |
| copyright | 版权声明 | 是 | 推荐 |
| encoder | 编码器标识 | 是 | 彩蛋位 |
| creation_time | 创建时间 | 是 | 自动生成 |

---

### 8.3 结构性 Metadata（udta / JSON）

该部分不保证被 MediaInfo 直接展示，但应可被 ffprobe 或播放器读取。

推荐字段：

```json
{
  "format": "encrypted_demo",
  "format_version": 1,
  "notice_duration": 8,
  "player": "demo_player",
  "purchase_url": "https://example.com"
}
```

---

## 9. metadata.txt → udta.json 自动转换

### 9.1 设计目的

- 提供**人类可编辑**的文本配置
- 自动生成**结构化、机器友好**的 JSON 数据
- 保证信息的一致性与可复用性

---

### 9.2 转换规则

- 白名单字段 → 写入 MP4 标准 metadata
- 结构字段（以 `x-` 或 `struct.` 前缀）→ 写入 udta.json
- 未识别字段：忽略并警告

示例：

```text
title=加密课程示例
comment=本文件包含加密内容
struct.notice_duration=8
struct.purchase_url=https://example.com
```

生成：

```json
{
  "notice_duration": 8,
  "purchase_url": "https://example.com"
}
```

---

## 10. 播放器信息展示设计（无 GUI）

### 10.1 设计理念

播放器不直接在命令行打印全部 Metadata，而是：

- 将关键信息暴露给**操作系统层**
- 通过任务栏 / 程序信息展示
- 减少 CLI 噪音，提升“真实播放器”质感

---

### 10.2 信息展示内容

建议展示以下摘要信息：

- Title
- Author / Artist
- 简要版权说明

---

### 10.3 不同平台的实现思路（非强制）

- Windows：
  - 设置进程窗口标题
  - 设置任务栏程序描述

- macOS：
  - 设置应用进程名
  - Dock / App Switcher 显示 Title

- Linux：
  - 设置窗口 WM_CLASS / 标题

该功能为**体验增强项**，不影响核心播放流程。

---

## 11. 可扩展方向（非本 Demo 实现）

- GUI 播放器（Qt / Electron）
- 授权文件 / 到期时间
- 多分辨率试看 + 加密正片
- 与服务器交互的密钥管理

---

## 10. 总结

本 Demo 的核心价值不在于“强保护”，而在于：

- 理解视频流与容器的区别
- 理解加密边界的工程设计
- 学会如何**友好而合规地提示版权信息**

这是一个适合作为课程项目、技术验证或工程实验的设计方案。

