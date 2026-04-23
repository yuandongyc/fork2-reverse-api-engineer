"""
OpenCode TUI 聊天工具
在底部状态栏显示当前模型

用法: uv run --with requests --with rich python chat_tui.py
"""

import requests
import time

BASE_URL = "http://localhost:4096"


def get_config():
    """获取当前配置"""
    try:
        resp = requests.get(f"{BASE_URL}/config", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except:
        return None


def get_current_model():
    """从 /config/providers 获取默认模型"""
    try:
        resp = requests.get(f"{BASE_URL}/config/providers", timeout=5)
        if resp.status_code == 200 and resp.text.strip():
            data = resp.json()
            defaults = data.get("default", {})
            if defaults and isinstance(defaults, dict):
                # 取第一个默认模型
                for provider, model in defaults.items():
                    return f"{provider}/{model}"
    except:
        pass

    # 备用：从 config 中的 agent 获取
    config = get_config()
    if config:
        agent_config = config.get("agent", {})
        if isinstance(agent_config, dict):
            for agent_name, agent_info in agent_config.items():
                if isinstance(agent_info, dict) and "model" in agent_info:
                    return agent_info["model"]

    return "未知模型"


def create_session(title="TUI Chat"):
    try:
        resp = requests.post(f"{BASE_URL}/session", json={"title": title}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def delete_session(session_id):
    try:
        resp = requests.delete(f"{BASE_URL}/session/{session_id}", timeout=5)
        return resp.status_code in (200, 204)
    except:
        return False


def send_message(session_id, text):
    url = f"{BASE_URL}/session/{session_id}/message"
    try:
        resp = requests.post(url, json={"parts": [{"type": "text", "text": text}]}, timeout=30)
        return resp.status_code == 200
    except:
        return False


def get_messages(session_id):
    url = f"{BASE_URL}/session/{session_id}/message"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and resp.text.strip():
            return resp.json()
        return []
    except:
        return []


def wait_for_reply(session_id, last_msg_id=None, timeout=60):
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


def extract_model_from_message(msg):
    """从消息中提取模型信息"""
    info = msg.get("info", {})
    # 尝试不同的可能字段
    if "model" in info:
        return info["model"]
    if "modelID" in info:
        if "providerID" in info:
            return f"{info['providerID']}/{info['modelID']}"
        return info["modelID"]
    return None


def format_message(msg):
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

    console = Console()

    # 获取当前模型
    current_model = get_current_model()

    # 标题
    console.print()
    console.print(
        Panel.fit(
            f"[bold blue]OpenCode TUI 聊天工具[/bold blue]  [dim]{current_model}[/dim]",
            subtitle="输入消息开始对话，/quit 退出，/model 查看模型",
            border_style="blue",
        )
    )
    console.print()

    # 创建会话
    console.print("[dim]正在创建会话...[/dim]", end="")
    session = create_session("TUI Chat Session")
    if "error" in session:
        console.print(f"\r[red]创建会话失败: {session['error']}[/red]")
        return

    session_id = session.get("id")
    console.print(f"\r[dim]会话已创建，模型: {current_model}[/dim]")
    console.print()

    last_msg_id = None

    try:
        while True:
            # 底部状态栏
            console.print(f"[dim]{'━' * console.width}[/dim]")
            console.print(f"[dim]模型: {current_model}  │  会话: {session_id[:8] if session_id else 'N/A'}...[/dim]")
            console.print()

            # 用户输入
            try:
                user_input = Prompt.ask("[bold green]你[/bold green]")
            except EOFError:
                break

            # 处理命令
            if user_input.strip() == "/quit":
                break
            if user_input.strip() == "/model":
                console.print(f"[dim]当前模型: {current_model}[/dim]")
                console.print(f"[dim]配置中的模型: {get_current_model()}[/dim]\n")
                continue
            if user_input.strip() == "/debug":
                config = get_config()
                if config:
                    agents = config.get("agent", {})
                    console.print("[dim]Agent 列表及模型:[/dim]")
                    for name, info in agents.items():
                        if isinstance(info, dict) and "model" in info:
                            console.print(f"[dim]  {name}: {info['model']}[/dim]")
                console.print()
                continue

            if not user_input.strip():
                continue

            # 显示用户消息
            console.print(Panel(user_input, border_style="green", padding=(0, 1)))

            # 发送消息并等待回复
            with console.status("[bold yellow]AI 正在思考...[/bold yellow]"):
                if not send_message(session_id, user_input):
                    console.print("[red]发送失败[/red]")
                    continue

                reply_msg = wait_for_reply(session_id, last_msg_id, timeout=60)

            if reply_msg:
                last_msg_id = reply_msg.get("info", {}).get("id")
                content = format_message(reply_msg)
                console.print(Panel(content, border_style="blue", padding=(1, 2)))

                # 从回复中提取模型并更新
                model_from_msg = extract_model_from_message(reply_msg)
                if model_from_msg:
                    current_model = model_from_msg
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
