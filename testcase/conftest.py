import pytest
from requests import Response

from api.client.user_api import ClientUserApi
from common.config import settings
from common.http_client import HttpClient
from common.token_manager import client_token_manager
from common.logger import setup_logging, get_logger

from common.http_logging import (
    format_http_details,
    log_http_response,
)

logger = get_logger("testcase")


def pytest_addoption(parser):
    parser.addoption(
        "--no-log-file",
        action="store_true",
        default=False,
        help="不生成日志文件，仅由pytest捕获日志",
    )

def pytest_configure(config):
    no_log_file = config.getoption("--no-log-file")
    setup_logging(
        write_to_file=not no_log_file,
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """保存测试用例各执行阶段的结果。"""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
@pytest.fixture
def log_http(request):
    """
    输出当前被测接口的日志。

    默认只输出摘要，用例失败时自动输出完整详情；
    details=True时立即输出完整详情。
    """

    recorded_response: Response | None = None
    recorded_title: str | None = None
    details_logged = False
    recorded_max_body_chars = 10_000

    def _log(
        response: Response,
        *,
        title: str | None = None,
        details: bool = False,
        include_headers: bool = False,
        max_body_chars: int = 10_000,
    ) -> None:
        nonlocal recorded_response
        nonlocal recorded_title
        nonlocal details_logged
        nonlocal recorded_max_body_chars

        log_http_response(
            response,
            title=title,
            details=details,
            include_headers=include_headers,
            max_body_chars=max_body_chars,
        )

        recorded_response = response
        recorded_title = title
        details_logged = details
        recorded_max_body_chars = max_body_chars

    yield _log

    try:
        report = getattr(request.node, "rep_call", None)

        if (
                report is not None
                and report.failed
                and recorded_response is not None
                and not details_logged
        ):
            detail_message = format_http_details(
                recorded_response,
                title=f"{recorded_title or 'HTTP请求'} - 失败详情",
                include_headers=True,
                max_body_chars=recorded_max_body_chars,
            )

            logger.error(
                "用例执行失败：%s\n%s",
                request.node.nodeid,
                detail_message,
            )
    except Exception:
        # 日志处理本身发生异常时，不覆盖原始测试失败。
        logger.exception(
            "生成HTTP失败详情时发生异常：%s",
            request.node.nodeid,
        )



@pytest.fixture(scope="session")
def client_token() -> str:
    """
    整个测试会话只执行一次登录。
    """
    return client_token_manager.get_token()


@pytest.fixture(scope="session")
def client_http(client_token: str):
    """
    已携带客户端 Token 的 HTTP 客户端。
    """
    client = HttpClient(
        base_url=settings["base_url"],
        token=client_token,
    )

    yield client

    client.close()


@pytest.fixture(scope="session")
def client_user_api(client_http: HttpClient):
    """
    已登录的客户端 User API 对象。
    """
    return ClientUserApi(client_http)