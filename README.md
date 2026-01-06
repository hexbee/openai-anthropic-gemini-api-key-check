# API Key Check

通过列出模型来验证 OpenAI、Anthropic 和 Gemini 的 API Key 是否有效。

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

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_BASE_URL=https://api.anthropic.com

# Gemini Configuration
GEMINI_API_KEY=xxx
```

## 使用方法

### 列出模型

```bash
# 列出 OpenAI 模型
uv run main.py openai

# 列出 Anthropic 模型
uv run main.py anthropic

# 列出 Gemini 模型
uv run main.py gemini
```

### 仅验证 API Key

```bash
uv run main.py openai --validate
uv run main.py anthropic -v
uv run main.py gemini -v
```

### 使用自定义参数

```bash
# 使用自定义 API Key（覆盖 .env）
uv run main.py openai --api-key sk-xxx

# 使用自定义 Base URL（覆盖 .env）
uv run main.py openai --base-url https://custom.api.com/v1

# 组合使用
uv run main.py openai -k sk-xxx -b https://custom.api.com/v1
```

## 命令行参数

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `provider` | - | 必选，可选值：`openai`、`anthropic`、`gemini` |
| `--api-key` | `-k` | API Key（覆盖 .env 配置） |
| `--base-url` | `-b` | Base URL（覆盖 .env 配置） |
| `--validate` | `-v` | 仅验证 API Key，不列出模型 |

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
