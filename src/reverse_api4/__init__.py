"""
reverse_api4 - 反向 API 分析工具
捕获应用的 API 调用，分析并生成客户端代码
"""

from .models import (
    APIEndpoint,
    AuthInfo,
    APICall,
    AnalysisResult,
    GeneratedCode,
    SessionInfo,
)
from .capturer import APICapturer, capture_api_calls
from .analyzer import analyze_api_calls, analyze, print_analysis_result
from .generator import (
    generate_python_client,
    generate_api_doc,
    generate_openapi_spec,
    generate_all,
)
from .cli import run_analysis, quick_capture

__version__ = "0.1.0"
__all__ = [
    # 模型
    "APIEndpoint",
    "AuthInfo",
    "APICall",
    "AnalysisResult",
    "GeneratedCode",
    "SessionInfo",
    # 捕获器
    "APICapturer",
    "capture_api_calls",
    # 分析器
    "analyze_api_calls",
    "analyze",
    "print_analysis_result",
    # 生成器
    "generate_python_client",
    "generate_api_doc",
    "generate_openapi_spec",
    "generate_all",
    # CLI
    "run_analysis",
    "quick_capture",
]
