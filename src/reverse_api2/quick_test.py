"""
快速测试 OpenCode API
用法: uv run --with requests python quick_test.py
查看 quick_test_output.txt 查看结果
"""

import requests
import sys
import traceback

BASE_URL = "http://localhost:4096"
OUTPUT_FILE = "quick_test_output.txt"


def main():
    f = open(OUTPUT_FILE, "w", encoding="utf-8")
    sys.stdout = f
    sys.stderr = f

    try:
        # 测试1: 获取当前项目
        print("=== 测试1: 获取当前项目 ===")
        resp = requests.get(f"{BASE_URL}/project/current", timeout=5)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.text[:500]}")
        print()

        # 测试2: 创建会话
        print("=== 测试2: 创建会话 ===")
        resp = requests.post(f"{BASE_URL}/session", json={"title": "test"}, timeout=5)
        print(f"状态码: {resp.status_code}")
        session = resp.json()
        session_id = session.get("id")
        print(f"会话ID: {session_id}")
        print()

        if not session_id:
            print("创建会话失败，退出")
            return

        # 测试3: 发送消息
        print("=== 测试3: 发送消息 ===")
        try:
            resp = requests.post(f"{BASE_URL}/session/{session_id}/prompt", json={"parts": [{"type": "text", "text": "你好"}]}, timeout=10)
            print(f"状态码: {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('content-type')}")
            print(f"响应长度: {len(resp.text)}")
            print(f"响应内容: {repr(resp.text[:500])}")
        except Exception as e:
            print(f"发送消息错误: {e}")
            traceback.print_exc()
        print()

        # 测试4: 获取消息列表
        print("=== 测试4: 获取消息列表 ===")
        try:
            resp = requests.get(f"{BASE_URL}/session/{session_id}/messages", timeout=5)
            print(f"状态码: {resp.status_code}")
            messages = resp.json()
            print(f"消息数量: {len(messages) if isinstance(messages, list) else 'N/A'}")
            print(f"消息预览: {repr(str(messages)[:500])}")
        except Exception as e:
            print(f"获取消息错误: {e}")
            traceback.print_exc()
        print()

        # 测试5: 删除会话
        print("=== 测试5: 删除会话 ===")
        resp = requests.delete(f"{BASE_URL}/session/{session_id}", timeout=5)
        print(f"状态码: {resp.status_code}")
        print()

        print("=== 完成 ===")

    except Exception as e:
        print(f"未预期的错误: {e}")
        traceback.print_exc()
    finally:
        f.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        print(f"测试完成，结果保存在 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
