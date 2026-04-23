# OpenCode TUI 聊天工具

基于 `reverse_api2` 的 Python 客户端，使用 `rich` 库实现美观的终端聊天界面。

## 前置条件

1. OpenCode 已运行（默认端口 4096）
2. 启动 OpenCode: `opencode`

## 依赖安装

```bash
# 使用 uv 安装依赖
uv pip install requests rich

# 或使用项目方式
uv init
uv add requests rich
```

## 使用方法

```bash
# 直接运行（uv 自动处理依赖）
uv run --with requests --with rich python chat_tui.py
```

## 功能特性

- 美观的终端界面（使用 rich 库）
- 实时显示 AI 思考状态
- 支持多轮对话
- 自动清理会话（退出时删除）
- 输入 `/quit` 退出

## 界面说明

```
┌─────────────────────────────────┐
│     OpenCode TUI 聊天工具      │
│     输入消息开始对话，/quit 退出  │
└─────────────────────────────────┘

[你] 你好！

┌─────────────────────────────────┐
│ 你好！我是 opencode...         │
└─────────────────────────────────┘
```

## 与 reverse_api2 的区别

| 特性 | reverse_api2 | reverse_api3 |
|-----|-------------|-------------|
| 类型 | API 客户端库 | TUI 聊天工具 |
| 界面 | 无（代码调用） | 终端界面 |
| 依赖 | requests | requests + rich |
| 用途 | 编程调用 API | 交互式聊天 |

## 代码结构

```
reverse_api3/
├── chat_tui.py      # 主程序
└── README.md       # 本文件
```

## 故障排除

**无法连接 OpenCode**
- 确保 OpenCode 正在运行：`opencode`
- 检查端口 4096 是否被占用
- 检查是否设置了 `OPENCODE_SERVER_PASSWORD`（需要认证）

**rich 库未安装**
```bash
uv pip install rich
# 或
uv run --with requests --with rich python chat_tui.py
```
