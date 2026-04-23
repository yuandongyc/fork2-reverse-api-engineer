"""
最小测试：直接测试 OpenCode API
用法: uv run --with requests python test_api.py
"""

import requests

BASE_URL = "http://localhost:4096"


def main():
    import sys

    # 将输出也写入文件
    f = open("test_output.txt", "w", encoding="utf-8")

    def log(msg):
        print(msg)
        f.write(str(msg) + "\n")
        f.flush()

    log("=== 测试 1: 获取当前项目 ===")
    try:
        resp = requests.get(f"{BASE_URL}/project/current", timeout=5)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.text[:200]}")
    except Exception as e:
        print(f"错误: {e}")
        return

    print("\n=== 测试 2: 创建会话 ===")
    try:
        resp = requests.post(f"{BASE_URL}/session", json={"title": "test"}, timeout=5)
        print(f"状态码: {resp.status_code}")
        session = resp.json()
        session_id = session.get("id")
        print(f"会话 ID: {session_id}")
    except Exception as e:
        print(f"错误: {e}")
        return

    if not session_id:
        print("创建会话失败")
        return

    print("\n=== 测试 3: 发送消息 ===")
    try:
        resp = requests.post(f"{BASE_URL}/session/{session_id}/prompt", json={"parts": [{"type": "text", "text": "你好"}]}, timeout=30)
        print(f"状态码: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type')}")
        print(f"响应长度: {len(resp.text)}")
        print(f"响应内容前200字符: {repr(resp.text[:200])}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n=== 测试 4: 删除会话 ===")
    try:
        resp = requests.delete(f"{BASE_URL}/session/{session_id}", timeout=5)
        print(f"状态码: {resp.status_code}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n完成！")


if __name__ == "__main__":
    main()
