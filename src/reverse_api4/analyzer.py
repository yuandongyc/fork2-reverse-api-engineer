"""
API 分析模块
调用 OpenCode API 分析 API 调用，生成分析报告
"""

import json
import re
import time
import requests
from typing import List, Optional

from .models import APIEndpoint, APICall, AnalysisResult


BASE_URL = "http://localhost:4096"


def _create_session(title: str = "Reverse API Analysis") -> Optional[str]:
    """创建 OpenCode 会话，返回 session_id"""
    try:
        resp = requests.post(f"{BASE_URL}/session", json={"title": title}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("id")
    except Exception as e:
        print(f"[分析器] 创建会话失败: {e}")
        return None


def _delete_session(session_id: str) -> None:
    """删除会话"""
    try:
        requests.delete(f"{BASE_URL}/session/{session_id}", timeout=5)
    except:
        pass


def _send_message(session_id: str, text: str, timeout: int = 60) -> bool:
    """发送消息"""
    try:
        resp = requests.post(f"{BASE_URL}/session/{session_id}/message", json={"parts": [{"type": "text", "text": text}]}, timeout=timeout)
        return resp.status_code == 200
    except Exception as e:
        print(f"[分析器] 发送消息失败: {e}")
        return False


def _get_messages(session_id: str) -> list:
    """获取消息列表"""
    try:
        resp = requests.get(f"{BASE_URL}/session/{session_id}/message", timeout=5)
        if resp.status_code == 200 and resp.text.strip():
            return resp.json()
        return []
    except:
        return []


def _wait_for_reply(session_id: str, last_msg_id: Optional[str] = None, timeout: int = 60) -> Optional[dict]:
    """等待 AI 回复"""
    start = time.time()
    while time.time() - start < timeout:
        messages = _get_messages(session_id)
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


def _format_api_calls(api_calls: List[APICall]) -> str:
    """将 API 调用格式化为文本，用于发送"""
    lines = ["以下是捕获到的 API 调用列表：\n"]
    for call in api_calls:
        ep = call.endpoint
        lines.append(f"=== API 调用 #{call.sequence} ===")
        lines.append(f"方法: {ep.method}")
        lines.append(f"URL: {ep.url}")
        # 只保留有意义的请求头
        if ep.headers:
            meaningful = {
                k: v for k, v in ep.headers.items() if any(k.lower().startswith(p) for p in ("authorization", "content-type", "accept", "x-"))
            }
            if meaningful:
                lines.append(f"请求头: {json.dumps(meaningful, ensure_ascii=False)[:200]}")
        if ep.body:
            body_preview = str(ep.body)[:200]
            lines.append(f"请求体: {body_preview}")
        if ep.response_status:
            lines.append(f"响应状态: {ep.response_status}")
        if ep.response_body:
            resp_preview = str(ep.response_body)[:300]
            lines.append(f"响应体预览: {resp_preview}")
        lines.append("")
    return "\n".join(lines)


def _parse_analysis_result(ai_text: str) -> AnalysisResult:
    """解析 AI 回复，尝试解析为 OpenAPI JSON"""
    result = AnalysisResult()

    # 尝试解析为 JSON
    try:
        # 去除可能的 markdown 代码块标记
        text = ai_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)

        # 解析为 OpenAPI 格式
        if "paths" in data:
            endpoints = []
            paths = data.get("paths", {})
            for path, methods in paths.items():
                for method, info in methods.items():
                    ep = APIEndpoint(
                        method=method.upper(),
                        url=path,
                        # 这里可以扩展，从 info 里提取更多信息
                    )
                    endpoints.append(ep)
            result.endpoints = endpoints

        # 解析认证信息
        if "security" in data:
            # OpenAPI security 定义
            result.auth_info = AuthInfo(type="unknown")

        result.summary = f"解析到 {len(result.endpoints)} 个端点（从 AI JSON）"

    except json.JSONDecodeError:
        # 解析失败，使用原始文本
        result.summary = ai_text[:500]
        result.raw_response = ai_text

    return result


def analyze_api_calls(api_calls: List[APICall]) -> Optional[AnalysisResult]:
    """
    调用 OpenCode API 分析 API 调用

    Args:
        api_calls: 捕获到的 API 调用列表

    Returns:
        AnalysisResult 或 None（失败）
    """
    if not api_calls:
        print("[分析器] 没有可分析的 API 调用")
        return None

    session_id = _create_session()
    if not session_id:
        return None

    try:
        # 格式化 API 调用数据（只保留有意义的头）
        api_text = _format_api_calls(api_calls)

        # 构造分析提示词：让 AI 输出 OpenAPI 3.0 JSON
        prompt = f"""请分析以下捕获的 API 调用，生成一个完整的 OpenAPI 3.0 规范 JSON。

{api_text}

要求：
1. 输出必须是**纯 JSON**，不要包含 markdown 代码块标记（不要 ```json）
2. 格式必须是有效的 OpenAPI 3.0，包含以下结构：
{{
  "openapi": "3.0.0",
  "info": {{"title": "API Analysis", "version": "1.0.0"}},
  "servers": [],
  "paths": {{
    "/path": {{
      "get": {{
        "summary": "描述",
        "parameters": [],
        "responses": {{"200": {{"description": "成功"}}}}
      }}
    }}
  }}

3. 从捕获的数据中提取：
   - 所有唯一的端点（去重）
   - 请求方法、URL、请求头（只保留有意义的，如 Authorization、Content-Type）
   - 请求参数和请求体结构
   - 响应状态码和示例

4. 如果某个字段无法确定，使用默认值或留空字符串。

直接输出 JSON，不要有任何其他说明文字。
"""

        print(f"[分析器] 正在发送 {len(api_calls)} 个 API 调用给 OpenCode...")

        # 发送分析请求
        if not _send_message(session_id, prompt):
            print("[分析器] 发送分析请求失败")
            return None

        # 等待回复
        print("[分析器] 等待 AI 分析...")
        reply_msg = _wait_for_reply(session_id, timeout=120)

        if not reply_msg:
            print("[分析器] 等待回复超时")
            return None

        # 提取回复文本
        parts = reply_msg.get("parts", [])
        ai_text = ""
        for part in parts:
            if part.get("type") == "text":
                ai_text += part.get("text", "") + "\n"

        if not ai_text:
            print("[分析器] 未获取到 AI 回复文本")
            return None

        print(f"[分析器] 分析完成，回复长度: {len(ai_text)} 字符")

        # 解析分析结果
        result = _parse_analysis_result(ai_text)

        # 直接使用捕获的端点（更可靠）
        if not result.endpoints:
            print("[分析器] 使用捕获的端点信息")
            result.endpoints = [call.endpoint for call in api_calls]

        # 保存 AI 分析摘要
        result.summary = ai_text[:500]
        result.raw_response = ai_text

        return result

    finally:
        _delete_session(session_id)


def print_analysis_result(result: AnalysisResult) -> None:
    """打印分析结果"""
    if not result:
        print("[分析器] 无分析结果")
        return

    print(f"\n{'=' * 60}")
    print("API 分析结果")
    print(f"{'=' * 60}")

    print(f"\n摘要:\n{result.summary[:300]}...\n")

    if result.endpoints:
        print(f"识别到 {len(result.endpoints)} 个端点:")
        for ep in result.endpoints:
            print(f"  - {ep.method} {ep.url}")

    if result.auth_info:
        print(f"\n认证方式: {result.auth_info.type}")

    print(f"\n原始回复长度: {len(result.raw_response)} 字符")
    print(f"{'=' * 60}\n")


# 便捷函数
def analyze(target_url: str, api_calls: List[APICall]) -> Optional[AnalysisResult]:
    """
    便捷函数：分析目标 URL 的 API 调用

    Args:
        target_url: 目标 URL（用于上下文）
        api_calls: API 调用列表

    Returns:
        AnalysisResult 或 None
    """
    print(f"[分析器] 开始分析 {target_url} 的 API...")
    return analyze_api_calls(api_calls)
