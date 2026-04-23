"""
检查 OpenCode API 端点
用法: uv run --with requests python check_api.py
"""

import requests
import base64

BASE_URL = "http://localhost:4096"

# 尝试带认证和不带认证
auth_header = None
# 如果需要认证，取消下面注释并填入密码
# auth_header = {"Authorization": "Basic " + base64.b64encode(b"opencode:password").decode()}

endpoints = [
    ("GET", "/project/current", None),  # 已知可工作
    ("GET", "/global/health", None),
    ("GET", "/doc", None),
    ("GET", "/session", None),
    ("POST", "/session", {"title": "test"}),
]

print("测试端点（不带认证）:\n")

for method, path, body in endpoints:
    url = BASE_URL + path
    try:
        headers = {"Content-Type": "application/json"}
        if auth_header:
            headers.update(auth_header)

        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=5, allow_redirects=False)
        else:
            resp = requests.post(url, json=body, headers=headers, timeout=5, allow_redirects=False)

        print(f"{method} {path}")
        print(f"  状态码: {resp.status_code}")

        text = resp.text.strip()
        if text.startswith("<!"):
            print(f"  响应: HTML")
            print(f"  前150字符: {repr(text[:150])}")
        else:
            print(f"  响应: {text[:200]}")
        print()

    except Exception as e:
        print(f"{method} {path}")
        print(f"  错误: {e}\n")

print("\n提示:")
print("1. 如果只有 /project/current 工作，可能需要认证")
print("2. 检查是否设置了 OPENCODE_SERVER_PASSWORD 环境变量")
print("3. 在浏览器访问 http://localhost:4096/project/current 确认")
