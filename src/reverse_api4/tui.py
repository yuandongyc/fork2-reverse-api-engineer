"""
reverse_api4 TUI 界面
交互式界面：输入应用 URL，自动开始反向 API 分析
"""

import sys
import os
import json
from pathlib import Path

# 添加父目录到路径，以便导入 reverse_api4 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text

from reverse_api4.capturer import APICapturer
from reverse_api4.analyzer import analyze_api_calls, print_analysis_result
from reverse_api4.generator import generate_all

console = Console()


def print_header():
    """打印标题"""
    console.print()
    console.print(
        Panel.fit(
            "[bold blue]reverse_api4[/bold blue] - [dim]反向 API 分析工具[/dim]", subtitle="输入应用 URL，自动捕获并分析 API", border_style="blue"
        )
    )
    console.print()


def get_user_input():
    """获取用户输入"""
    console.print("[bold]请输入要分析的应用信息：[/bold]")

    # 输入 URL
    while True:
        target_url = Prompt.ask("[bold green]应用 URL[/bold green]")
        if target_url.strip():
            break
        console.print("[red]URL 不能为空[/red]")

    # 可选参数
    console.print("\n[dim]可选参数（直接回车使用默认值）：[/dim]")

    duration_str = Prompt.ask("[dim]捕获时长（秒）[/dim]", default="5")  # 改成 5 秒快速测试
    duration = int(duration_str) if duration_str.strip() else 5

    output_dir = Prompt.ask("[dim]输出目录[/dim]", default="./output")

    headless_str = Prompt.ask("[dim]无头模式？(y/n)[/dim]", default="y")
    headless = headless_str.lower() != "n"

    console.print()
    return {
        "target_url": target_url.strip(),
        "duration": duration,
        "output_dir": output_dir.strip(),
        "headless": headless,
    }


def _sample_api_calls():
    """生成示例 API 调用（当用户捕获到 0 个时）"""
    from reverse_api4.models import APICall, APIEndpoint

    calls = []
    # 示例 1：GitHub API 根端点
    calls.append(
        APICall(
            endpoint=APIEndpoint(
                method="GET",
                url="https://api.github.com/user",
                headers={"Authorization": "token ghp_xxxx", "Accept": "application/vnd.github.v3+json"},
                response_status=200,
                response_body=json.dumps({"login": "example", "id": 12345}, ensure_ascii=False),
            ),
            sequence=1,
        )
    )

    # 示例 2：获取仓库
    calls.append(
        APICall(
            endpoint=APIEndpoint(
                method="GET",
                url="https://api.github.com/repos/octocat/Hello-World",
                headers={"Accept": "application/vnd.github.v3+json"},
                response_status=200,
                response_body=json.dumps({"name": "Hello-World", "description": "My first repo", "stars": 5}, ensure_ascii=False),
            ),
            sequence=2,
        )
    )

    # 示例 3：搜索仓库
    calls.append(
        APICall(
            endpoint=APIEndpoint(
                method="GET",
                url="https://api.github.com/search/repositories?q=tetris+language:assembly&sort=stars&order=desc",
                headers={"Accept": "application/vnd.github.v3+json"},
                response_status=200,
                response_body=json.dumps({"total_count": 1, "items": []}, ensure_ascii=False),
            ),
            sequence=3,
        )
    )

    return calls


def run_analysis(config):
    """运行分析流程"""
    target_url = config["target_url"]
    duration = config["duration"]
    output_dir = config["output_dir"]
    headless = config["headless"]

    console.print(Panel(f"目标: {target_url}", border_style="blue"))
    console.print()

    # 步骤 1：捕获 API
    console.print("[bold]步骤 1/4: 捕获 API 调用...[/bold]")
    capturer = APICapturer(headless=headless, timeout=duration * 1000)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("正在访问并捕获 API...", total=duration)
        api_calls = capturer.capture(target_url, duration=duration)
        progress.update(task, completed=duration)

    if not api_calls:
        console.print("[yellow]⚠️ 未捕获到 API 调用，使用示例数据继续演示[/yellow]")
        api_calls = _sample_api_calls()
        console.print(f"[green]✓[/green] 使用 {len(api_calls)} 个示例 API 调用")

    capturer.api_calls = api_calls
    capturer.print_summary()

    # 步骤 2：分析 API
    console.print("\n[bold]步骤 2/4: 分析 API 调用...[/bold]")
    console.print("[dim]正在调用 OpenCode 分析...[/dim]")

    analysis = analyze_api_calls(api_calls)

    if not analysis:
        console.print("[red]分析失败[/red]")
        return False

    console.print("[green]✓[/green] 分析完成")
    print_analysis_result(analysis)

    # 步骤 3：生成代码
    console.print("\n[bold]步骤 3/4: 生成代码和文档...[/bold]")

    if not analysis.endpoints:
        console.print("[yellow]⚠️ 未识别到端点，使用示例端点[/yellow]")
        # 从 api_calls 手动添加端点
        from reverse_api4.models import APIEndpoint

        analysis.endpoints = [call.endpoint for call in api_calls]

    outputs = generate_all(analysis, class_name="GitHubAPIClient", title=f"API for {target_url}")

    # 保存输出
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    client_file = output_path / "api_client.py"
    client_file.write_text(outputs["client_code"], encoding="utf-8")
    console.print(f"[green]✓[/green] Python 客户端: {client_file}")

    doc_file = output_path / "API_DOC.md"
    doc_file.write_text(outputs["api_doc"], encoding="utf-8")
    console.print(f"[green]✓[/green] API 文档: {doc_file}")

    if outputs.get("openapi_spec"):
        spec_file = output_path / "openapi.json"
        spec_file.write_text(outputs["openapi_spec"], encoding="utf-8")
        console.print(f"[green]✓[/green] OpenAPI spec: {spec_file}")

    # 步骤 4：完成
    console.print(f"\n[bold]步骤 4/4: 完成！[/bold]")
    console.print(
        Panel.fit(
            f"[bold green]分析完成！[/bold green]\n输出目录: {output_path.absolute()}\n共处理 {len(api_calls)} 个 API 调用", border_style="green"
        )
    )

    return True


def check_playwright():
    """检查 Playwright 是否已安装（检测 .venv）"""
    try:
        import playwright
        from playwright.async_api import async_playwright

        # 检查当前是否运行在 .venv 虚拟环境中
        venv_path = Path(__file__).parent.parent.parent / ".venv"
        using_venv = False
        if venv_path.exists() and venv_path.is_dir():
            playwright_pkg = venv_path / "Lib" / "site-packages" / "playwright"
            if playwright_pkg.exists():
                using_venv = True

        # 检查浏览器二进制文件（通常在用户目录下）
        home = Path.home()
        playwright_browser_dir = home / "AppData" / "Local" / "ms-playwright"

        if playwright_browser_dir.exists():
            chromium_dirs = list(playwright_browser_dir.glob("chromium*"))
            if chromium_dirs:
                browser_info = f"找到 Chromium: {chromium_dirs[0]}"
                if using_venv:
                    return True, f"虚拟环境 .venv 中可用 - {browser_info}"
                else:
                    return True, browser_info

        # 浏览器未找到
        if using_venv:
            return False, "在 .venv 中检测到 Playwright，但浏览器未安装。请运行: playwright install chromium"
        else:
            return False, "未找到 Chromium，请运行: playwright install chromium"

    except ImportError:
        return False, "Playwright 未安装。请运行: uv pip install playwright"


def main():
    """主函数"""
    print_header()

    # 检查环境
    available, msg = check_playwright()
    if not available:
        console.print(f"[red]错误: {msg}[/red]")
        console.print("\n[yellow]请运行以下命令安装:[/yellow]")
        console.print("  uv pip install playwright")
        console.print("  playwright install chromium")
        return

    console.print(f"[dim]环境检查通过: {msg}[/dim]\n")

    try:
        while True:
            config = get_user_input()

            console.print("\n[dim]即将开始分析...[/dim]")
            if not Confirm.ask("确认开始？", default=True):
                break

            success = run_analysis(config)

            if not success:
                console.print("\n[red]分析失败，请重试[/red]")

            if not Confirm.ask("\n是否分析另一个应用？", default=True):
                break

    except KeyboardInterrupt:
        console.print("\n[yellow]已中断[/yellow]")

    console.print("\n[bold green]再见！[/bold green]\n")


if __name__ == "__main__":
    main()
