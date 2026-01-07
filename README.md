# API Key Check

多提供商 AI CLI 工具，支持 OpenAI、Anthropic 和 Gemini。可验证 API Key、列出模型、同时与多个提供商聊天。

## 安装

```bash
uv sync
```

## 配置

复制 `.env.example` 为 `.env` 并填写你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_SYSTEM_PROMPT=You are a helpful assistant.
OPENAI_DEFAULT_MODEL=gpt-4o

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_SYSTEM_PROMPT=You are a helpful assistant.
ANTHROPIC_DEFAULT_MODEL=claude-sonnet-4-20250514

# Gemini Configuration
GEMINI_API_KEY=xxx
GEMINI_SYSTEM_PROMPT=You are a helpful assistant.
GEMINI_DEFAULT_MODEL=gemini-2.0-flash
```

## 使用方法

### 列出模型

```bash
uv run main.py list openai      # 列出 OpenAI 模型
uv run main.py list anthropic   # 列出 Anthropic 模型
uv run main.py list gemini      # 列出 Gemini 模型
```

### 验证 API Key

```bash
uv run main.py list openai --validate
uv run main.py list anthropic -v
uv run main.py list gemini -v
```

### 使用自定义参数

```bash
# 使用自定义 API Key（覆盖 .env）
uv run main.py list openai --api-key sk-xxx

# 使用自定义 Base URL（覆盖 .env）
uv run main.py list openai --base-url https://custom.api.com/v1

# 组合使用
uv run main.py list openai -k sk-xxx -b https://custom.api.com/v1
```

### 与提供商聊天

```bash
# 同时与所有提供商聊天（流式输出）
uv run main.py chat "Hello, how are you?"

# 只与特定提供商聊天
uv run main.py chat "Hello" -p openai
uv run main.py chat "Hello" -p anthropic
uv run main.py chat "Hello" -p gemini

# 指定模型
uv run main.py chat "Tell me a joke" -m gpt-4o

# 使用自定义系统提示
uv run main.py chat "Hello" -s "You are a pirate"
```

## 命令行参数

### `list` 命令

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `provider` | - | 必选，可选值：`openai`、`anthropic`、`gemini` |
| `--api-key` | `-k` | API Key（覆盖 .env 配置） |
| `--base-url` | `-b` | Base URL（覆盖 .env 配置） |
| `--validate` | `-v` | 仅验证 API Key，不列出模型 |

### `chat` 命令

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `message` | - | 必选，发送给提供商的消息 |
| `--provider` | `-p` | 指定提供商（默认：所有提供商） |
| `--model` | `-m` | 指定模型（覆盖 .env 默认模型） |
| `--system-prompt` | `-s` | 系统提示（覆盖 .env 系统提示） |

## 项目结构

```
.
├── .env.example          # 环境变量示例
├── .gitignore
├── pyproject.toml        # 项目配置
├── README.md
├── main.py               # 主入口 (CLI)
└── providers/
    ├── __init__.py       # 模块导出
    ├── base.py           # 基类 BaseProvider
    ├── openai_provider.py
    ├── anthropic_provider.py
    └── gemini_provider.py
```

## 依赖

- openai
- anthropic
- google-genai
- python-dotenv
- rich
