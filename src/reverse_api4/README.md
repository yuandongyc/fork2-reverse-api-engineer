# reverse_api4 - 反向 API 分析工具

通过浏览器自动化捕获目标应用的 API 调用，使用 OpenCode AI 分析并生成客户端代码。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| API 捕获 | 使用 Playwright 拦截浏览器中的 API 请求 |
| 智能过滤 | 自动过滤静态资源（JS、CSS、图片等） |
| AI 分析 | 调用 OpenCode API 分析 API 调用模式 |
| 代码生成 | 自动生成 Python requests 风格客户端 |
| 文档生成 | 输出 Markdown API 文档和 OpenAPI 规范 |

---

## 前置条件

### 1. OpenCode 正在运行

```bash
opencode serve
```

### 2. 安装依赖（推荐 uv 方式）

```bash
cd D:\MyProjects\c_projects\fork2-reverse-api-engineer
uv pip install playwright requests rich
uv run playwright install chromium
```

---

## 使用方法

### 交互式 TUI 界面（推荐）

```bash
cd D:\MyProjects\c_projects\fork2-reverse-api-engineer\src\reverse_api4
uv run --with requests --with rich --with playwright python tui.py
```

**界面流程：**
1. 启动后输入要分析的应用 URL（如 `https://api.github.com`）
2. 可选设置捕获时长、输出目录等参数
3. 确认后自动开始：捕获 → 分析 → 生成代码
4. 查看输出目录中的结果

---

### 命令行模式

```bash
# 完整分析流程
uv run python -m reverse_api4 run https://api.github.com

# 指定输出目录
uv run python -m reverse_api4 run https://weather.com --output ./weather_api

# 有头模式（可见浏览器）
uv run python -m reverse_api4 run https://example.com --headless false

# 调整捕获时长（秒）
uv run python -m reverse_api4 run https://example.com --duration 60

# 仅捕获模式（不分析）
uv run python -m reverse_api4 capture https://github.com/trending
https://api.github.com/users/github  
```

#### 命令行参数

**run 命令：**

| 参数 | 说明 | 默认值 |
|------|------|------|
| `url` | 目标 URL（必需） | - |
| `--output DIR` | 输出目录 | `./output` |
| `--headless true/false` | 无头模式 | `true` |
| `--duration SECONDS` | 捕获时长（秒） | `30` |

**capture 命令：**

| 参数 | 说明 | 默认值 |
|------|------|------|
| `url` | 目标 URL（必需） | - |
| `--headless true/false` | 无头模式 | `true` |
| `--duration SECONDS` | 捕获时长（秒） | `30` |

---

## 输出文件

运行后会在输出目录生成：

```
output/
├── api_client.py      # Python requests 风格客户端
├── API_DOC.md         # Markdown API 文档
└── openapi.json       # OpenAPI 3.0 规范（可选）
```

---

## 作为模块使用

```python
from reverse_api4 import capture_api_calls, analyze, generate_all

# 1. 捕获 API 调用
api_calls = capture_api_calls("https://example.com", headless=True, duration=30)

# 2. 分析
result = analyze("https://example.com", api_calls)

# 3. 生成代码
outputs = generate_all(result, class_name="MyAPIClient")
print(outputs["client_code"])
```

---

## 模块说明

| 模块 | 功能 |
|------|------|
| `models.py` | 数据模型定义（APIEndpoint, AnalysisResult 等） |
| `capturer.py` | API 捕获（Playwright 浏览器自动化） |
| `analyzer.py` | 调用 OpenCode API 进行 AI 分析 |
| `generator.py` | 生成 Python 客户端和文档 |
| `cli.py` | 命令行接口 |
| `tui.py` | 交互式 TUI 界面 |
| `__init__.py` | 包导出 |

---

## 工作流程

```
目标 URL
   │
   ▼
[Playwright 浏览器] ──► 访问应用，拦截请求
   │
   ▼
[API 捕获器] ──► 过滤 + 结构化 API 调用
   │
   ▼
[OpenCode 分析] ──► AI 分析端点、参数、认证
   │
   ▼
[代码生成器] ──► Python 客户端 + API 文档
```

---

## 示例

### 分析 GitHub API

```bash
uv run python -m reverse_api4 run https://api.github.com --output ./github_api
```

输出：
- `github_api/api_client.py` - GitHub API 客户端
- `github_api/API_DOC.md` - API 文档
- `github_api/openapi.json` - OpenAPI 规范

---

## 与 reverse_api 的区别

| 特性 | reverse_api | reverse_api4 |
|------|-------------|-------------|
| AI 引擎 | Claude Agent SDK | OpenCode HTTP API |
| 结构 | 单仓库多模块 | 清晰模块化 |
| 浏览器 | Playwright | Playwright（保留） |
| 输出 | Python 脚本 | API 文档 + Python 客户端 |
| 界面 | CLI | CLI + TUI 交互界面 |

---

## 故障排除

### 无法连接 OpenCode
- 确保 OpenCode 正在运行：`opencode`
- 检查端口 4096：`curl http://localhost:4096/project/current`

### Playwright 未安装
```bash
uv pip install playwright
uv run playwright install chromium
```

### 未捕获到 API 调用
- 增加 `--duration` 参数
- 使用 `--headless false` 观察浏览器行为
- 检查目标 URL 是否正确

---

## 开发计划

详见 `PLAN.md` 了解完整设计思路。

---

## 作者

基于 [fork2-reverse-api-engineer](D:\MyProjects\c_projects\fork2-reverse-api-engineer) 项目的 reverse_api 重构版本。
