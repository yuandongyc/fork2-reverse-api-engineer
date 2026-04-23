"""
命令行接口
提供 CLI 命令来运行反向 API 分析
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional

from .models import SessionInfo, APIEndpoint, AnalysisResult, GeneratedCode
from .capturer import APICapturer
from .analyzer import analyze_api_calls, print_analysis_result
from .generator import generate_all, generate_python_client, generate_api_doc


def print_banner():
    """打印欢迎信息"""
    print("=" * 60)
    print("  reverse_api4 - API 反向分析工具")
    print("  捕获 + 分析 + 生成代码")
    print("=" * 60)
    print()


def run_analysis(
    target_url: str, output_dir: str = "./output", headless: bool = True, capture_duration: int = 30, session_title: str = "Reverse API Analysis"
) -> Optional[SessionInfo]:
    """
    运行完整的反向 API 分析流程

    Args:
        target_url: 目标 URL
        output_dir: 输出目录
        headless: 是否无头模式
        capture_duration: 捕获持续时间（秒）
        session_title: OpenCode 会话标题

    Returns:
        SessionInfo 或 None（失败）
    """
    session = SessionInfo(target_url=target_url, mode="engineer")
    session.start_time = "开始分析..."

    print(f"\n[1/4] 捕获 API 调用...")
    print(f"  目标: {target_url}")
    print(f"  无头模式: {headless}")
    print(f"  捕获时长: {capture_duration}秒")

    capturer = APICapturer(headless=headless, timeout=capture_duration * 1000)
    api_calls = capturer.capture(target_url, duration=capture_duration)
    session.api_calls = api_calls

    if not api_calls:
        print("[错误] 未捕获到任何 API 调用")
        return None

    print(f"  捕获到 {len(api_calls)} 个 API 调用")

    # 打印捕获摘要
    capturer.api_calls = api_calls
    capturer.print_summary()

    print(f"\n[2/4] 分析 API 调用...")
    print(f"  使用 OpenCode 分析 {len(api_calls)} 个调用...")

    analysis = analyze_api_calls(api_calls)
    session.analysis = analysis

    if not analysis:
        print("[错误] 分析失败")
        return None

    print_analysis_result(analysis)

    print(f"\n[3/4] 生成代码和文档...")
    code_outputs = generate_all(analysis, class_name="GeneratedAPIClient", title=f"API for {target_url}")
    session.output = GeneratedCode(**code_outputs)

    # 保存输出
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 保存 Python 客户端
    client_file = output_path / "api_client.py"
    client_file.write_text(code_outputs["client_code"], encoding="utf-8")
    print(f"  Python 客户端: {client_file}")

    # 保存 API 文档
    doc_file = output_path / "API_DOC.md"
    doc_file.write_text(code_outputs["api_doc"], encoding="utf-8")
    print(f"  API 文档: {doc_file}")

    # 保存 OpenAPI spec
    if code_outputs.get("openapi_spec"):
        spec_file = output_path / "openapi.json"
        spec_file.write_text(code_outputs["openapi_spec"], encoding="utf-8")
        print(f"  OpenAPI spec: {spec_file}")

    print(f"\n[4/4] 完成！")
    print(f"  输出目录: {output_path.absolute()}")
    session.end_time = "分析完成"

    return session


def quick_capture(target_url: str, headless: bool = True, duration: int = 30):
    """快速捕获模式：只捕获不分析"""
    print(f"快速捕获模式: {target_url}")

    capturer = APICapturer(headless=headless)
    api_calls = capturer.capture(target_url, duration=duration)

    print(f"捕获到 {len(api_calls)} 个 API 调用:\n")
    capturer.api_calls = api_calls
    capturer.print_summary()

    # 保存为 JSON
    output = []
    for call in api_calls:
        ep = call.endpoint
        output.append(
            {
                "sequence": call.sequence,
                "method": ep.method,
                "url": ep.url,
                "status": ep.response_status,
                "content_type": ep.resource_type,
            }
        )

    output_file = "captured_apis.json"
    Path(output_file).write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n已保存: {output_file}")


def main():
    """CLI 入口"""
    print_banner()

    # 简单参数解析
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print_help()
        return

    command = args[0]

    if command == "run":
        # 完整分析流程
        if len(args) < 2:
            print("错误: 请指定目标 URL")
            print("用法: python -m reverse_api4 run <url> [--output DIR] [--headless true|false]")
            return

        target_url = args[1]
        output_dir = "./output"
        headless = True
        duration = 30

        # 解析可选参数
        i = 2
        while i < len(args):
            if args[i] == "--output" and i + 1 < len(args):
                output_dir = args[i + 1]
                i += 2
            elif args[i] == "--headless" and i + 1 < len(args):
                headless = args[i + 1].lower() == "true"
                i += 2
            elif args[i] == "--duration" and i + 1 < len(args):
                duration = int(args[i + 1])
                i += 2
            else:
                i += 1

        run_analysis(target_url=target_url, output_dir=output_dir, headless=headless, capture_duration=duration)

    elif command == "capture":
        # 仅捕获
        if len(args) < 2:
            print("错误: 请指定目标 URL")
            return
        target_url = args[1]
        headless = True
        duration = 30

        i = 2
        while i < len(args):
            if args[i] == "--headless" and i + 1 < len(args):
                headless = args[i + 1].lower() == "true"
                i += 2
            elif args[i] == "--duration" and i + 1 < len(args):
                duration = int(args[i + 1])
                i += 2
            else:
                i += 1

        quick_capture(target_url, headless=headless, duration=duration)

    else:
        print(f"未知命令: {command}")
        print_help()


def print_help():
    """打印帮助信息"""
    print("用法:")
    print("  python -m reverse_api4 run <url>           # 完整分析")
    print("  python -m reverse_api4 capture <url>      # 仅捕获")
    print()
    print("选项:")
    print("  --output DIR       输出目录（默认: ./output）")
    print("  --headless true|false   无头模式（默认: true）")
    print("  --duration SECONDS   捕获时长（默认: 30）")
    print()
    print("示例:")
    print("  python -m reverse_api4 run https://api.github.com")
    print("  python -m reverse_api4 capture https://example.com --duration 60")
    print("  python -m reverse_api4 run https://weather.com --output ./weather_api")


if __name__ == "__main__":
    main()
