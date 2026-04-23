# reverse_api4 实现计划

## 目标
重新实现 `reverse_api` 的功能——**对输入的应用进行反向 API 分析**：
1. 通过浏览器自动化访问目标应用
2. 拦截/捕获应用发出的 HTTP API 调用
3. 使用 OpenCode AI 分析这些 API 调用
4. 生成 API 文档或 Python 客户端代码

---

## 一、原有 reverse_api 功能分析

| 模块 | 功能 |
|------|------|
| `cli.py` | 命令行界面，支持 manual/agent/engineer/collector 模式 |
| `engineer.py` | 使用 Claude SDK 分析 HAR 文件，生成 Python API 脚本 |
| `browser.py` | Playwright 浏览器自动化，访问目标应用 |
| `collector.py` | 数据收集器，收集 API 调用信息 |
| `base_engineer.py` | 基础工程类 |
| `playwright_codegen.py` | Playwright 代码生成 |
| `session.py` | 会话管理 |

---

## 二、reverse_api4 改进方向

### 与 reverse_api 的区别
| 特性 | reverse_api | reverse_api4 |
|------|-----------|-------------|
| AI 引擎 | Claude Agent SDK | OpenCode HTTP API（借鉴 reverse_api2/3） |
| 结构 | 单仓库多模块 | 更清晰的模块化设计 |
| 浏览器 | Playwright | Playwright（保留） |
| 输出 | Python 脚本 | API 文档 + Python 客户端 |

---

## 三、模块划分

### 1. `cli.py` - 命令行接口
```bash
python -m reverse_api4 run https://example.com --mode engineer
python -m reverse_api4 run ./path/to/app --output ./output
```

### 2. `capturer.py` - API 捕获模块
- 使用 Playwright 启动浏览器
- 拦截网络请求（route interception 或 HAR 记录）
- 过滤出有意义的 API 调用（排除静态资源）
- 输出：结构化的 API 调用列表

### 3. `analyzer.py` - API 分析模块（调用 OpenCode）
- 将捕获的 API 调用发送给 OpenCode
- 使用 OpenCode API（reverse_api2/3 的方式）
- 让 AI 分析：端点、参数、认证方式、数据格式
- 输出：API 分析报告

### 4. `generator.py` - 代码生成模块
- 根据分析报告生成 Python API 客户端
- 可选生成：requests 风格 / httpx 风格 / OpenAPI spec

### 5. `browser.py` - 浏览器管理（借鉴 reverse_api）
- Playwright 启动和管理
- 支持手动操作（manual mode）和自动导航（agent mode）

---

## 四、工作流程

```
输入: 目标应用 (URL 或本地路径)
  │
  ▼
[浏览器自动化] ──► 访问应用，拦截 API 调用
  │
  ▼
[API 捕获] ──► 过滤 + 结构化 API 调用数据
  │
  ▼
[OpenCode 分析] ──► 发送捕获数据给 OpenCode API
  │                    (使用 reverse_api2/3 的客户端)
  ▼
[生成输出] ──► API 文档 + Python 客户端代码
```

---

## 五、文件结构

```
reverse_api4/
├── __init__.py
├── cli.py           # 命令行接口
├── capturer.py      # API 捕获（Playwright）
├── analyzer.py      # API 分析（调用 OpenCode）
├── generator.py     # 代码生成
├── browser.py       # 浏览器管理
├── models.py        # 数据模型
├── utils.py         # 工具函数
├── examples/
│   ├── analyze_github.py
│   └── analyze_weather_api.py
├── output/          # 生成的代码输出目录
├── PLAN.md         # 本文件
└── README.md       # 使用说明
```

---

## 六、实现顺序

1. [ ] `models.py` - 定义数据结构（APIEndpoint, AuthInfo 等）
2. [ ] `capturer.py` - API 捕获功能
3. [ ] `analyzer.py` - 调用 OpenCode API 分析（借鉴 reverse_api2/3）
4. [ ] `generator.py` - 代码生成
5. [ ] `browser.py` - 浏览器管理
6. [ ] `cli.py` - 命令行接口
7. [ ] `README.md` - 文档

---

## 七、关键技术点

### 1. API 捕获方式
- **HAR 文件**：Playwright 可生成 HAR，然后解析
- **请求拦截**：使用 `page.route()` 拦截 XHR/fetch 请求
- **选择**：先实现 HAR 方式（更简单）

### 2. 调用 OpenCode
- 使用 reverse_api2/3 已验证的 API 客户端
- 端点：`/session/:id/message`
- 发送捕获的 API 数据，让 AI 分析并生成代码

### 3. 输出格式
- Markdown API 文档
- Python requests 风格客户端
- OpenAPI 3.0 spec（可选）

---

## 八、使用示例

```bash
# 安装依赖
uv pip install playwright requests rich
playwright install chromium

# 分析某个网站的 API
uv run python -m reverse_api4 run https://weather.com

# 指定输出目录
uv run python -m reverse_api4 run https://api.github.com --output ./github_api

# 使用 agent 模式（自动导航并捕获）
uv run python -m reverse_api4 run https://example.com --mode agent
```

---

请确认这个计划是否符合你的预期？
