import json
import logging
from typing import Any, Mapping
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)

from requests import Response

from common.logger import get_logger


logger = get_logger("http")


# 请求头中需要脱敏的字段
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "proxy-authorization",
}

# 请求体、响应体、URL 查询参数中需要脱敏的字段
SENSITIVE_FIELDS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "client_secret",
}

# 详情日志中保留的请求头
IMPORTANT_REQUEST_HEADERS = {
    "content-type",
    "accept",
    "user-agent",
    "x-request-id",
    "trace-id",
}

# 详情日志中保留的响应头
IMPORTANT_RESPONSE_HEADERS = {
    "content-type",
    "content-length",
    "x-request-id",
    "trace-id",
}


def _redact_headers(
    headers: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """对请求头或响应头中的敏感字段进行脱敏。"""

    if not headers:
        return {}

    return {
        key: (
            "***"
            if str(key).lower() in SENSITIVE_HEADERS
            else value
        )
        for key, value in dict(headers).items()
    }


def _select_headers(
    headers: Mapping[str, Any] | None,
    allowed_headers: set[str],
) -> dict[str, Any]:
    """筛选需要记录的请求头或响应头，并对敏感字段脱敏。"""

    if not headers:
        return {}

    selected_headers = {}

    for key, value in dict(headers).items():
        lower_key = str(key).lower()

        if lower_key not in allowed_headers:
            continue

        selected_headers[key] = (
            "***"
            if lower_key in SENSITIVE_HEADERS
            else value
        )

    return selected_headers


def _redact_sensitive_fields(data: Any) -> Any:
    """递归脱敏字典或列表中的敏感字段。"""

    if isinstance(data, dict):
        return {
            key: (
                "***"
                if str(key).lower() in SENSITIVE_FIELDS
                else _redact_sensitive_fields(value)
            )
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            _redact_sensitive_fields(item)
            for item in data
        ]

    if isinstance(data, tuple):
        return tuple(
            _redact_sensitive_fields(item)
            for item in data
        )

    return data


def _format_body(
    body: Any,
    max_chars: int = 10_000,
) -> str:
    """格式化请求体或响应体，并限制最大输出字符数。"""

    if body is None:
        return "<empty>"

    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")

    if isinstance(body, str):
        try:
            data = json.loads(body)
        except (TypeError, ValueError):
            text = body
        else:
            data = _redact_sensitive_fields(data)
            text = json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
    else:
        try:
            data = _redact_sensitive_fields(body)
            text = json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        except (TypeError, ValueError):
            text = str(body)

    if len(text) <= max_chars:
        return text

    omitted_chars = len(text) - max_chars

    return (
        f"{text[:max_chars]}\n"
        f"... 已省略 {omitted_chars} 个字符"
    )


def _format_url(
    url: str,
    *,
    include_host: bool = False,
) -> str:
    """
    格式化URL。

    include_host=False时只显示接口路径和查询参数。
    URL查询参数中的敏感字段会自动脱敏。
    """

    if not url:
        return "<unknown>"

    parts = urlsplit(url)

    query_parameters = parse_qsl(
        parts.query,
        keep_blank_values=True,
    )

    redacted_parameters = [
        (
            key,
            "***" if key.lower() in SENSITIVE_FIELDS else value,
        )
        for key, value in query_parameters
    ]

    redacted_query = urlencode(
        redacted_parameters,
        doseq=True,
    )

    if include_host:
        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                redacted_query,
                parts.fragment,
            )
        )

    path = parts.path or "/"

    if redacted_query:
        path = f"{path}?{redacted_query}"

    return path


def _indent_text(
    text: str,
    spaces: int = 4,
) -> str:
    """为多行文本增加统一缩进。"""

    prefix = " " * spaces

    return "\n".join(
        f"{prefix}{line}"
        for line in text.splitlines()
    )


def _extract_business_summary(response: Response) -> str:
    """
    从JSON响应中提取常用业务字段。

    默认提取：
    code、success、message。
    """

    try:
        response_data = response.json()
    except ValueError:
        return ""

    if not isinstance(response_data, dict):
        return ""

    summary_parts = []

    if "code" in response_data:
        summary_parts.append(
            f"code={response_data['code']}"
        )

    if "success" in response_data:
        summary_parts.append(
            f"success={response_data['success']}"
        )

    if "message" in response_data:
        message = str(response_data["message"])
        message = message.replace("\r", " ").replace("\n", " ")

        if len(message) > 100:
            message = f"{message[:100]}..."

        summary_parts.append(f"message={message}")

    if not summary_parts:
        return ""

    return " | " + " | ".join(summary_parts)


def format_http_summary(
    response: Response,
    *,
    title: str | None = None,
    include_host: bool = False,
) -> str:
    """将请求结果格式化为一行摘要日志。"""

    request = response.request

    if request is None:
        raise ValueError("Response中不存在对应的Request对象")

    title_text = f"[{title}] " if title else ""

    request_url = _format_url(
        request.url,
        include_host=include_host,
    )

    business_summary = _extract_business_summary(response)

    return (
        f"{title_text}"
        f"{request.method} {request_url} "
        f"-> HTTP {response.status_code} | "
        f"{response.elapsed.total_seconds():.3f}s"
        f"{business_summary}"
    )


def format_http_details(
    response: Response,
    *,
    title: str | None = None,
    include_headers: bool = False,
    include_all_headers: bool = False,
    max_body_chars: int = 10_000,
) -> str:
    """
    将请求和响应格式化为详细日志。

    Args:
        response: requests响应对象。
        title: 接口或业务场景名称。
        include_headers: 是否显示请求头和响应头。
        include_all_headers: 是否显示全部请求头和响应头。
            只有include_headers=True时生效。
        max_body_chars: 请求体和响应体最大字符数。

    Returns:
        格式化后的日志字符串。
    """

    request = response.request

    if request is None:
        raise ValueError("Response中不存在对应的Request对象")

    try:
        response_body = response.json()
    except ValueError:
        response_body = response.text

    request_body_text = _format_body(
        request.body,
        max_chars=max_body_chars,
    )

    response_body_text = _format_body(
        response_body,
        max_chars=max_body_chars,
    )

    display_title = title or "HTTP请求详情"

    lines = [
        "",
        f"========== {display_title} ==========",
        "Request",
        f"  Method : {request.method}",
        (
            "  URL    : "
            f"{_format_url(request.url, include_host=True)}"
        ),
    ]

    if include_headers:
        if include_all_headers:
            request_headers = _redact_headers(
                request.headers
            )
        else:
            request_headers = _select_headers(
                request.headers,
                IMPORTANT_REQUEST_HEADERS,
            )

        lines.extend(
            [
                "  Headers:",
                _indent_text(
                    _format_body(request_headers),
                    spaces=4,
                ),
            ]
        )

    lines.extend(
        [
            "  Body:",
            _indent_text(
                request_body_text,
                spaces=4,
            ),
            "",
            "Response",
            f"  Status : {response.status_code}",
            (
                "  Time   : "
                f"{response.elapsed.total_seconds():.3f}s"
            ),
        ]
    )

    if include_headers:
        if include_all_headers:
            response_headers = _redact_headers(
                response.headers
            )
        else:
            response_headers = _select_headers(
                response.headers,
                IMPORTANT_RESPONSE_HEADERS,
            )

        lines.extend(
            [
                "  Headers:",
                _indent_text(
                    _format_body(response_headers),
                    spaces=4,
                ),
            ]
        )

    lines.extend(
        [
            "  Body:",
            _indent_text(
                response_body_text,
                spaces=4,
            ),
            "=" * (22 + len(display_title)),
        ]
    )

    return "\n".join(lines)


def log_http_response(
    response: Response,
    *,
    title: str | None = None,
    details: bool = False,
    include_headers: bool = False,
    include_all_headers: bool = False,
    include_host_in_summary: bool = False,
    max_body_chars: int = 10_000,
    summary_level: int = logging.INFO,
    detail_level: int = logging.DEBUG,
) -> None:
    """
    记录HTTP请求结果。
    默认只记录一行INFO摘要。
    details=True时，额外记录完整请求响应详情。

    Args:
        response: requests响应对象。
        title: 接口或业务场景名称。
        details: 是否输出完整请求响应详情。
        include_headers: 详情中是否显示Header。
        include_all_headers: 是否显示全部Header。
        include_host_in_summary: 摘要中是否显示域名和端口。
        max_body_chars: 请求体和响应体最大字符数。
        summary_level: 摘要日志等级，默认INFO。
        detail_level: 详情日志等级，默认DEBUG。
    """

    if logger.isEnabledFor(summary_level):
        summary_message = format_http_summary(
            response=response,
            title=title,
            include_host=include_host_in_summary,
        )

        logger.log(
            summary_level,
            summary_message,
        )

    if not details:
        return

    if not logger.isEnabledFor(detail_level):
        return

    detail_message = format_http_details(
        response=response,
        title=title,
        include_headers=include_headers,
        include_all_headers=include_all_headers,
        max_body_chars=max_body_chars,
    )

    logger.log(
        detail_level,
        detail_message,
    )