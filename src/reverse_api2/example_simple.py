"""
简单的 OpenCode API 调用示例
使用方法: python example_simple.py
"""

import requests
import json


BASE_URL = "http://localhost:4096"


def main():
    print("OpenCode Python 示例")
    print("=" * 40)

    try:
        # 1. 检查连接 - 获取当前项目
        print("\n[1] 检查 OpenCode 连接...")
        resp = requests.get(f"{BASE_URL}/project/current")
        resp.raise_for_status()
        project = resp.json()
        print(f"✓ 已连接")
        print(f"  项目路径: {project.get('data', {}).get('worktree', 'N/A')}")

        # 2. 创建会话
        print("\n[2] 创建新会话...")
        resp = requests.post(f"{BASE_URL}/session", json={"title": "Python API 测试"})
        resp.raise_for_status()
        session = resp.json()
        session_id = session["data"]["id"]
        print(f"✓ 会话已创建: {session_id}")

        # 3. 发送消息
        print("\n[3] 发送消息到 AI...")
        resp = requests.post(
            f"{BASE_URL}/session/{session_id}/prompt",
            json={
                "parts": [{"type": "text", "text": "你好！请用一句话介绍你自己。"}],
                "model": {"providerID": "anthropic", "modelID": "claude-opus-4-5-thinking"},
            },
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"✓ 收到响应")

        # 提取 AI 回复文本
        messages = result.get("data", {}).get("messages", [])
        if messages:
            for msg in messages:
                if msg.get("role") == "assistant":
                    parts = msg.get("parts", [])
                    for part in parts:
                        if part.get("type") == "text":
                            print(f"\nAI 回复:\n{part.get('text', '')}")

        # 4. 清理
        print("\n[4] 清理 - 删除会话...")
        resp = requests.delete(f"{BASE_URL}/session/{session_id}")
        resp.raise_for_status()
        print(f"✓ 会话已删除")

        print("\n" + "=" * 40)
        print("完成！")

    except requests.exceptions.ConnectionError:
        print("\n✗ 错误: 无法连接到 OpenCode Server")
        print("  请确保 OpenCode 正在运行 (命令: opencode)")
        print("  默认 API 端口: 4096")
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP 错误: {e}")
        print(f"  响应: {e.response.text}")
    except Exception as e:
        print(f"\n✗ 错误: {e}")


if __name__ == "__main__":
    main()
