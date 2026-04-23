"""
OpenCode API 完整示例
用法: uv run --with requests python example.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:4096"


def main():
    print("OpenCode Python API 示例\n")

    try:
        # 0. 获取并解析 API 文档
        print("[0] 获取 API 文档...")
        resp = requests.get(f"{BASE_URL}/doc", timeout=5)
        print(f"  /doc 状态码: {resp.status_code}")

        if resp.status_code == 200 and not resp.text.strip().startswith("<!"):
            print("  ✓ API 文档可访问")
            try:
                openapi = resp.json()
                paths = openapi.get("paths", {})
                print(f"  找到 {len(paths)} 个端点")

                # 查找发送消息的正确端点
                print("\n  查找发送消息的端点:")
                for path, methods in paths.items():
                    if "message" in path.lower() or "prompt" in path.lower():
                        for method in methods:
                            if method == "post":
                                summary = methods[method].get("summary", "")
                                print(f"    POST {path} - {summary}")
            except Exception as e:
                print(f"  解析失败: {e}")
        else:
            print(f"  ✗ 无法访问 /doc")
            print(f"  响应前150字符: {repr(resp.text[:150])}")
            print("\n  提示: 请确保 OpenCode 服务器已启动")
            return

        # 1. 检查连接
        print("[1] 检查连接...")
        resp = requests.get(f"{BASE_URL}/project/current", timeout=5)
        resp.raise_for_status()
        project = resp.json()
        print(f"  项目: {project.get('worktree', 'N/A')}")

        # 2. 创建会话
        print("\n[2] 创建会话...")
        resp = requests.post(f"{BASE_URL}/session", json={"title": "Python示例"}, timeout=5)
        resp.raise_for_status()
        session = resp.json()
        session_id = session.get("id")
        print(f"  会话 ID: {session_id}")

        if not session_id:
            print("  创建会话失败")
            return

        # 3. 先检查 API 文档端点
        print("\n[3] 检查 API 文档...")
        resp = requests.get(f"{BASE_URL}/doc", timeout=5)
        print(f"  /doc 状态码: {resp.status_code}")
        if not resp.text.strip().startswith("<!"):
            print("  ✓ API 文档可访问")
        else:
            print("  ✗ 返回 HTML，可能不是 API 端点")

        # 4. 发送消息（使用正确的端点 /session/:id/message）
        print("\n[4] 发送消息...")
        # 添加 Accept 头，明确请求 JSON
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        resp = requests.post(
            f"{BASE_URL}/session/{session_id}/message",
            json={"parts": [{"type": "text", "text": "你好！请用一句话介绍你自己。"}]},
            headers=headers,
            timeout=30,
        )
        print(f"  状态码: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('content-type', 'N/A')}")

        # 检查响应
        if resp.text.strip().startswith("<!"):
            print(f"  响应是 HTML，前200字符: {repr(resp.text[:200])}")
            print("\n  ⚠️ 警告: 服务器返回了 HTML 而不是 API 响应")
            print("  可能原因:")
            print("  1. OpenCode 未启用 HTTP API")
            print("  2. 需要认证 (OPENCODE_SERVER_PASSWORD)")
            print("  3. 访问 http://localhost:4096/doc 查看 API 文档")
            return

        # 尝试解析响应
        try:
            result = resp.json()
            print(f"  响应: {json.dumps(result, ensure_ascii=False)[:300]}")
        except:
            print(f"  响应内容: {repr(resp.text[:200])}")

        # 4. 等待并获取 AI 回复
        print("\n[4] 等待 AI 回复...")
        for i in range(15):  # 最多等待30秒
            time.sleep(2)
            resp = requests.get(f"{BASE_URL}/session/{session_id}/messages", timeout=5)
            resp.raise_for_status()
            messages = resp.json()

            if isinstance(messages, list) and len(messages) > 0:
                print(f"  找到 {len(messages)} 条消息")

                # 查找最后一条 assistant 消息
                for msg in reversed(messages):
                    role = msg.get("info", {}).get("role")
                    if role == "assistant":
                        parts = msg.get("parts", [])
                        for part in parts:
                            if part.get("type") == "text":
                                print(f"\n  AI 回复: {part.get('text', '')[:300]}")
                                break
                        break

                print("\n  完整消息:")
                print(json.dumps(messages, indent=2, ensure_ascii=False)[:800])
                break

            print(f"  等待中... ({i + 1}/15)")
        else:
            print("  超时，未收到 AI 回复")

        # 5. 清理
        print("\n[5] 清理 - 删除会话...")
        resp = requests.delete(f"{BASE_URL}/session/{session_id}", timeout=5)
        print(f"  删除状态: {resp.status_code}")

        print("\n=== 完成 ===")

    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到 OpenCode Server")
        print("请确保 OpenCode 正在运行 (命令: opencode)")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
