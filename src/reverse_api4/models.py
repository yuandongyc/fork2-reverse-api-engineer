"""
数据模型定义
定义反向 API 分析过程中使用的数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any


@dataclass
class APIEndpoint:
    """单个 API 端点信息"""

    method: str  # GET, POST, PUT, DELETE, etc.
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    body: Optional[Any] = None
    response_status: int = 0
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: Optional[Any] = None
    timestamps: str = ""
    resource_type: str = ""  # 资源类型：json, xml, html, etc.
    is_api: bool = True  # 是否是 API 调用（过滤静态资源后）


@dataclass
class AuthInfo:
    """认证信息"""

    type: str  # bearer, api-key, basic, oauth2, none
    location: str = ""  # header, query, cookie
    key_name: str = ""  # 如 Authorization, X-API-Key
    value: str = ""  # 仅用于测试，实际不保存敏感信息


@dataclass
class APICall:
    """一次完整的 API 调用记录"""

    endpoint: APIEndpoint
    request_id: str = ""
    resource_type: str = ""
    sequence: int = 0  # 调用顺序


@dataclass
class AnalysisResult:
    """OpenCode 分析结果"""

    endpoints: List[APIEndpoint] = field(default_factory=list)
    auth_info: Optional[AuthInfo] = None
    summary: str = ""
    raw_response: str = ""  # OpenCode 的原始回复


@dataclass
class GeneratedCode:
    """生成的代码输出"""

    client_code: str = ""  # Python 客户端代码
    api_doc: str = ""  # Markdown API 文档
    openapi_spec: str = ""  # OpenAPI 3.0 spec (可选)


@dataclass
class SessionInfo:
    """反向分析会话信息"""

    target_url: str
    mode: str = "engineer"  # manual, agent, engineer, collector
    session_id: str = ""  # OpenCode 会话 ID
    har_file: str = ""  # 捕获的 HAR 文件路径
    api_calls: List[APICall] = field(default_factory=list)
    analysis: Optional[AnalysisResult] = None
    output: Optional[GeneratedCode] = None
    start_time: str = ""
    end_time: str = ""
