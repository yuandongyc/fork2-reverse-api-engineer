# OpenCode Python API 客户端

模仿 https://learnopencode.com/5-advanced/10a-sdk-basics.html 的 JavaScript SDK，用 Python 实现。

## 前置条件

1. OpenCode 已安装并运行（默认 HTTP API 端口 4096）
2. 启动 OpenCode: `opencode`
3. 安装 uv（Python 包管理器）：
   - Windows (PowerShell): `irm https://astral.sh/uv/install.ps1 | iex`
   - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## 安装依赖

```bash
# 使用 uv 安装依赖
uv pip install requests

# 或使用项目方式（自动创建虚拟环境）
uv init
uv add requests
```

## 使用方法

### 基本用法

```python
from opencode_client import OpenCodeClient

client = OpenCodeClient(base_url="http://localhost:4096")

# 创建会话
session = client.session_create(title="我的任务")
session_id = session["data"]["id"]

# 发送消息
result = client.session_prompt(
    session_id=session_id,
    text="请帮我分析这段代码",
    model_provider="anthropic",
    model_id="claude-opus-4-5-thinking"
)

# 获取响应
print(result)
```

### 运行示例

```bash
# 基本示例（使用 uv 运行）
uv run python opencode_client.py basic

# 批量代码审查
uv run python opencode_client.py review

# 文件操作
uv run python opencode_client.py files

# 简单示例（无需提前安装依赖，uv 自动处理）
uv run --with requests python example_simple.py
```

## API 对照表

| JavaScript SDK | Python 方法 |
|---------------|------------|
| `client.session.list()` | `client.session_list()` |
| `client.session.create()` | `client.session_create(title)` |
| `client.session.get()` | `client.session_get(id)` |
| `client.session.prompt()` | `client.session_prompt(id, text)` |
| `client.file.read()` | `client.file_read(path)` |
| `client.find.files()` | `client.find_files(query)` |
| `client.config.get()` | `client.config_get()` |

## 注意事项

- 确保 OpenCode Server 正在运行（检查 localhost:4096）
- API 端点基于文档推断，实际端点可能有所不同
- 如需事件监听，OpenCode 使用 SSE（Server-Sent Events）
