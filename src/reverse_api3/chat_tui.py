"""
OpenCode TUI 聊天工具
使用 rich 库实现终端界面，与 OpenCode API 交互

用法:
  uv run --with requests --with rich python chat_tui.py
"""

import requests
import time

BASE_URL = "http://localhost:4096"


def create_session(title="TUI Chat"):
    """创建会话"""
    try:
        resp = requests.post(f"{BASE_URL}/session", json={"title": title}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def delete_session(session_id):
    """删除会话"""
    try:
        resp = requests.delete(f"{BASE_URL}/session/{session_id}", timeout=5)
        return resp.status_code in (200, 204)
    except:
        return False


def send_message(session_id, text):
    """发送消息"""
    url = f"{BASE_URL}/session/{session_id}/message"
    try:
        resp = requests.post(url, json={"parts": [{"type": "text", "text": text}]}, timeout=30)
        return resp.status_code == 200
    except:
        return False


def get_messages(session_id):
    """获取消息列表"""
    url = f"{BASE_URL}/session/{session_id}/message"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and resp.text.strip():
            return resp.json()
        return []
    except:
        return []


def wait_for_reply(session_id, last_msg_id=None, timeout=60):
    """等待 AI 回复"""
    start = time.time()
    while time.time() - start < timeout:
        messages = get_messages(session_id)
        if not messages:
            time.sleep(1)
            continue
        for msg in reversed(messages):
            role = msg.get("info", {}).get("role")
            msg_id = msg.get("info", {}).get("id")
            if role == "assistant" and msg_id != last_msg_id:
                return msg
        time.sleep(1)
    return None


def format_message(msg):
    """格式化消息为显示文本"""
    parts = msg.get("parts", [])
    lines = []
    for part in parts:
        if part.get("type") == "text":
            lines.append(part.get("text", ""))
        elif part.get("type") == "tool":
            tool_name = part.get("name", "unknown")
            lines.append(f"[调用工具: {tool_name}]")
    return "\n".join(lines)


def main():
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.text import Text

    console = Console()

    # 标题
    console.print()
    console.print(Panel.fit("[bold blue]OpenCode TUI 聊天工具[/bold blue]", subtitle="输入消息开始对话，/quit 退出", border_style="blue"))

    # 创建会话
    console.print("\n[dim]正在创建会话...[/dim]", end="")
    session = create_session("TUI Chat Session")
    if "error" in session:
        console.print(f"\r[red]创建会话失败: {session['error']}[/red]")
        return

    session_id = session.get("id")
    console.print(f"\r[dim]会话已创建: {session_id}[/dim]")
    console.print()

    last_msg_id = None

    try:
        while True:
            # 用户输入
            try:
                user_input = Prompt.ask("[bold green]你[/bold green]")
            except EOFError:
                break

            if user_input.strip() == "/quit":
                break

            if not user_input.strip():
                continue

            # 显示用户消息
            console.print(Panel(user_input, border_style="green", padding=(0, 1)))

            # 发送消息
            with console.status("[bold yellow]AI 正在思考...[/bold yellow]"):
                if not send_message(session_id, user_input):
                    console.print("[red]发送失败[/red]")
                    continue

                # 等待回复
                reply_msg = wait_for_reply(session_id, last_msg_id, timeout=60)

            if reply_msg:
                last_msg_id = reply_msg.get("info", {}).get("id")
                content = format_message(reply_msg)

                # 显示 AI 回复
                console.print(Panel(content, border_style="blue", padding=(1, 2)))
            else:
                console.print("[yellow]等待回复超时[/yellow]")

            console.print()

    except KeyboardInterrupt:
        console.print("\n[yellow]已中断[/yellow]")

    finally:
        # 清理会话
        console.print("\n[dim]正在清理会话...[/dim]", end="")
        if delete_session(session_id):
            console.print("\r[dim]会话已删除[/dim]")
        else:
            console.print("\r[dim]删除会话失败[/dim]")

        console.print("\n[bold green]再见！[/bold green]\n")


if __name__ == "__main__":
    main()
