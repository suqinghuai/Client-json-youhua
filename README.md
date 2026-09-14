# ChatRecordConverter

## 项目介绍

ChatRecordConverter 是一个聊天记录格式转换工具，能够将不同来源的聊天记录 JSON 文件转换为统一的 exporter 标准格式，便于后续查阅与分析。

**支持的输入格式：**
- **WeFlow** — 微信聊天记录导出格式（私聊/群聊）
- **QQChatExporter** — QQ 聊天记录导出格式（私聊/群聊）

**输出的统一格式包含：**
- 会话元信息（账号、对话对象、群聊标识等）
- 消息过滤配置
- 标准化消息列表（支持文本、图片、语音、视频、表情、文件、链接、引用、红包、转账、系统消息、通话等类型）

## 快速开始

### 面向使用者(使用exe文件)

1. 将 `main.exe` 放置在聊天记录 JSON 文件所在目录中
2. 双击运行 `main.exe`
3. 程序会自动扫描当前目录下所有可识别的聊天记录文件并转换
4. 转换结果输出为 `messages.json`（单文件时）或按文件名创建子目录（多文件时）
5. 也可通过命令行指定目录：`main.exe <目录路径>`

### 面向开发者（从源码运行）
```bash
# 克隆项目
git clone <项目地址>

# 进入项目目录
cd <项目目录>

# 激活虚拟环境
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py           # 转换当前目录下的聊天记录
python main.py <目录路径>  # 转换指定目录下的聊天记录
```

## 实现方法

程序核心流程如下：

1. **格式检测** — 读取 JSON 文件，通过关键字段（`weflow`/`session` 或 `metadata`/`chatInfo`）自动识别来源格式
2. **消息转换** — 根据检测到的格式调用对应的转换函数：
   - WeFlow → `convert_weflow_to_exporter()`：将 WeFlow 的 `localType` 映射为标准 `renderType`，提取发送者、时间、内容等字段
   - QQChatExporter → `convert_qqchat_to_exporter()`：将 QQ 的 `type`/`elements` 映射为标准 `renderType`，处理图片/视频/语音/文件等资源链接
3. **统一输出** — 生成包含 `schemaVersion`、`account`、`conversation`、`filters`、`messages` 的标准 JSON 结构

**消息类型映射：**

| renderType | 说明 | WeFlow localType | QQChatExporter type |
|---|---|---|---|
| text | 文本消息 | 1 | type_1 |
| image | 图片 | 3 | type_6/type_23/type_33 |
| voice | 语音 | 34 | type_34/audio |
| emoji | 表情 | 47 | type_47/face |
| video | 视频 | — | type_9/type_19/video |
| file | 文件 | 内容以`[文件]`开头 | type_2/file |
| link | 链接 | 内容以`[链接]`开头 | type_4/type_7 |
| quote | 引用回复 | — | type_3/reply |
| transfer | 转账 | 内容以`[转账]`开头 | — |
| redpacket | 红包 | 内容以`[红包]`开头 | — |
| voip | 通话 | 50 | type_25 |
| system | 系统消息 | 10000 | system=true |
| chathistory | 聊天记录 | 其他 | — |

**文件匹配规则：**
- 优先匹配特定模式：`私聊_*.json`、`群聊_*.json`、`friend_*.json`、`group_*.json`
- 若无匹配，则扫描目录下所有 `*.json` 文件

## 版本日志

### v1.0.0 (2026-09-13)

- 支持 WeFlow 格式聊天记录转换
- 支持 QQChatExporter 格式聊天记录转换
- 自动检测输入文件格式
- 支持文本、图片、语音、视频、表情、文件、链接、引用、红包、转账、系统消息、通话等消息类型
- 支持私聊与群聊
- 支持命令行指定工作目录
- 打包为 exe 可独立运行

## 许可证

本项目采用 Prosperity Public License 2.0.0 许可证，详见 LICENSE 文件。