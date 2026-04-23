"""
API 捕获模块
使用 Playwright 拦截目标应用的 API 调用
"""

import json
import asyncio
from typing import List, Optional
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, Request, Response

from .models import APIEndpoint, APICall


class APICapturer:
    """使用 Playwright 捕获 API 调用"""

    # 静态资源扩展名（需要过滤）
    STATIC_EXTENSIONS = {
        ".js",
        ".css",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".mp4",
        ".mp3",
        ".webp",
        ".avif",
    }

    # API 特征：响应 Content-Type 包含这些
    API_CONTENT_TYPES = {
        "application/json",
        "application/xml",
        "text/xml",
        "application/javascript",
    }

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.api_calls: List[APICall] = []
        self._sequence = 0

    async def _is_api_request(self, request: Request) -> bool:
        """判断是否是 API 请求（过滤静态资源）"""
        url = request.url

        # 过滤静态资源扩展名
        if any(url.endswith(ext) for ext in self.STATIC_EXTENSIONS):
            return False

        # 检查请求头中的 Accept
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return False

        # 检查域名：API 相关域名直接返回 True
        url_lower = url.lower()
        if any(domain in url_lower for domain in ["api.github.com", "collector.github.com", "graphql"]):
            return True

        # 检查 URL 模式（包含 api、graphql、rest、private 等）
        if any(keyword in url_lower for keyword in ["/api/", "/graphql", "/rest/", "/v1/", "/v2/", "/v3/", "/_private/"]):
            return True

        # 检查响应 Content-Type（如果有响应）
        try:
            response = await request.response()
            if response:
                content_type = response.headers.get("content-type", "").lower()
                if any(ct in content_type for ct in self.API_CONTENT_TYPES):
                    return True
                # 如果响应是 JSON，即使 Content-Type 不对也算
                if "json" in content_type:
                    return True
        except:
            pass

        return False

        # 检查请求头中的 Accept
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return False

        # 检查 URL 模式（包含 api、graphql、rest 等）
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in ["/api/", "/graphql", "/rest/", "/v1/", "/v2/", "/v3/"]):
            return True

        # 检查响应 Content-Type（如果有响应）
        try:
            response = await request.response()
            if response:
                content_type = response.headers.get("content-type", "").lower()
                if any(ct in content_type for ct in self.API_CONTENT_TYPES):
                    return True
                # 如果响应是 JSON，即使 Content-Type 不对也算
                if "json" in content_type:
                    return True
        except:
            pass

        return False

    async def _capture_request(self, request: Request):
        """捕获单个请求"""
        if not await self._is_api_request(request):
            return

        self._sequence += 1
        api_call = APICall(
            endpoint=APIEndpoint(
                method=request.method,
                url=request.url,
                headers=dict(request.headers),
                params=dict(request.url.split("?")[-1] if "?" in request.url else {}),
            ),
            request_id=f"req_{self._sequence}",
            sequence=self._sequence,
        )

        # 尝试获取请求体
        try:
            post_data = request.post_data
            if post_data:
                api_call.endpoint.body = post_data
        except:
            pass

        # 尝试获取响应
        try:
            response = await request.response()
            if response:
                api_call.endpoint.response_status = response.status
                api_call.endpoint.response_headers = dict(response.headers)

                # 尝试获取响应体
                try:
                    body = await response.text()
                    api_call.endpoint.response_body = body
                    api_call.endpoint.resource_type = "json" if "json" in response.headers.get("content-type", "") else "other"
                except:
                    pass
        except:
            pass

        self.api_calls.append(api_call)

    async def _run_capture(self, target_url: str, duration: int = 30):
        """运行捕获"""
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                record_har_path=None,  # 不自动记录 HAR
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            page: Page = await context.new_page()

            # 监听请求
            page.on("request", self._capture_request)

            print(f"[捕获器] 正在访问: {target_url}")
            try:
                await page.goto(target_url, wait_until="networkidle", timeout=self.timeout)
            except Exception as e:
                print(f"[捕获器] 页面加载完成（可能有超时）: {e}")

            # 等待额外时间以捕获动态加载的 API
            print(f"[捕获器] 等待 {duration} 秒以捕获动态 API 调用...")
            await asyncio.sleep(duration)

            # 尝试滚动页面以触发更多 API
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(2)
            except:
                pass

            await browser.close()
            print(f"[捕获器] 捕获完成，共 {len(self.api_calls)} 个 API 调用")

    def capture(self, target_url: str, duration: int = 30) -> List[APICall]:
        """
        捕获目标 URL 的 API 调用

        Args:
            target_url: 目标 URL
            duration: 捕获持续时间（秒），等待动态加载

        Returns:
            API 调用列表
        """
        self.api_calls = []
        self._sequence = 0

        asyncio.run(self._run_capture(target_url, duration))
        return self.api_calls

    def capture_and_save_har(self, target_url: str, har_path: str, duration: int = 30):
        """捕获并保存为 HAR 文件"""
        api_calls = self.capture(target_url, duration)

        # 转换为 HAR 格式
        har = {"log": {"version": "1.2", "creator": {"name": "reverse_api4", "version": "1.0"}, "entries": []}}

        for call in api_calls:
            entry = {
                "request": {
                    "method": call.endpoint.method,
                    "url": call.endpoint.url,
                    "headers": [{"name": k, "value": v} for k, v in call.endpoint.headers.items()],
                    "queryString": [{"name": k, "value": v} for k, v in call.endpoint.params.items()],
                    "postData": call.endpoint.body,
                },
                "response": {
                    "status": call.endpoint.response_status,
                    "headers": [{"name": k, "value": v} for k, v in call.endpoint.response_headers.items()],
                    "content": {"text": call.endpoint.response_body, "mimeType": call.endpoint.resource_type},
                },
            }
            har["log"]["entries"].append(entry)

        Path(har_path).write_text(json.dumps(har, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[捕获器] HAR 文件已保存: {har_path}")

        return api_calls

    def print_summary(self):
        """打印捕获摘要"""
        print(f"\n{'=' * 60}")
        print(f"捕获摘要: 共 {len(self.api_calls)} 个 API 调用")
        print(f"{'=' * 60}")

        for call in self.api_calls:
            ep = call.endpoint
            print(f"\n[{call.sequence}] {ep.method} {ep.url}")
            print(f"    状态: {ep.response_status}, 类型: {ep.resource_type}")
            if ep.response_body:
                body_preview = str(ep.response_body)[:100]
                print(f"    响应预览: {body_preview}...")

        print(f"\n{'=' * 60}\n")


# 便捷函数
def capture_api_calls(target_url: str, headless: bool = True, duration: int = 30) -> List[APICall]:
    """
    便捷函数：捕获 API 调用

    Args:
        target_url: 目标 URL
        headless: 是否无头模式
        duration: 捕获持续时间（秒）

    Returns:
        API 调用列表
    """
    capturer = APICapturer(headless=headless, timeout=30000)
    return capturer.capture(target_url, duration)
