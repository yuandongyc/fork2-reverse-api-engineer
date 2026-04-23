"""
OpenCode API Python Client
用法: uv run python opencode_client.py basic
"""

import requests
import json
import time

BASE_URL = "http://localhost:4096"


def get_messages(session_id, timeout=5):
    """获取会话消息列表 - GET /session/:id/message"""
    url = f"{BASE_URL}/session/{session_id}/message"
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return {"error": "http_error", "status_code": resp.status_code, "content": resp.text[:200]}
        if not resp.text.strip():
            return {"error": "empty_response"}
        if resp.text.strip().startswith("<!"):
            return {"error": "html_response", "content": resp.text[:300]}
        return resp.json()
    except Exception as e:
        return {"error": "exception", "message": str(e)}


def send_message(session_id, text, timeout=30):
    """发送消息 - POST /session/:id/message"""
    url = f"{BASE_URL}/session/{session_id}/message"
    body = {"parts": [{"type": "text", "text": text}]}
    try:
        resp = requests.post(url, json=body, timeout=timeout)
        return {"status_code": resp.status_code, "content": resp.text[:500], "headers": dict(resp.headers)}
    except Exception as e:
        return {"error": "exception", "message": str(e)}


def create_session(title="Python API Test"):
    """创建会话 - POST /session"""
    try:
        resp = requests.post(f"{BASE_URL}/session", json={"title": title}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def delete_session(session_id):
    """删除会话 - DELETE /session/:id"""
    try:
        resp = requests.delete(f"{BASE_URL}/session/{session_id}", timeout=5)
        return resp.status_code in (200, 204)
    except:
        return False


def get_project_current():
    """获取当前项目 - GET /project/current"""
    try:
        resp = requests.get(f"{BASE_URL}/project/current", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def example_basic():
    """基本使用示例"""
    print("OpenCode Python API 示例\n")

    try:
        # 1. 检查连接
        print("[1] 检查连接...")
        project = get_project_current()
        if "error" in project:
            print(f"  错误: {project['error']}")
            return
        print(f"  项目: {project.get('worktree', 'N/A')}")

        # 2. 创建会话
        print("\n[2] 创建会话...")
        session = create_session("Python API 测试")
        if "error" in session:
            print(f"  错误: {session['error']}")
            return
        session_id = session.get("id")
        print(f"  会话 ID: {session_id}")

        if not session_id:
            print("  创建会话失败")
            return

        # 3. 发送消息
        print("\n[3] 发送消息...")
        result = send_message(session_id, "你好！请用一句话介绍你自己。")
        print(f"  状态码: {result.get('status_code', 'N/A')}")
        print(f"  响应: {result.get('content', '')[:200]}")

        # 4. 等待获取 AI 回复
        print("\n[4] 等待 AI 回复...")
        for i in range(15):
            time.sleep(2)
            messages = get_messages(session_id)
            if isinstance(messages, list) and len(messages) > 0:
                print(f"  找到 {len(messages)} 条消息")
                for msg in reversed(messages):
                    role = msg.get("info", {}).get("role")
                    if role == "assistant":
                        parts = msg.get("parts", [])
                        for part in parts:
                            if part.get("type") == "text":
                                print(f"\n  AI 回复: {part.get('text', '')[:300]}")
                                break
                        break
                break
            print(f"  等待中... ({i + 1}/15)")
        else:
            print("  超时，未收到回复")

        # 5. 清理
        print("\n[5] 清理 - 删除会话...")
        if delete_session(session_id):
            print("  会话已删除")
        else:
            print("  删除失败")

        print("\n=== 完成 ===")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "basic":
        example_basic()
    else:
        print("用法: uv run python opencode_client.py basic")
