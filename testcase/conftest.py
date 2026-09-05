import pytest

from api.client.user_api import ClientUserApi
from common.config import settings
from common.http_client import HttpClient
from common.token_manager import client_token_manager
from common.logger import setup_logging, get_logger

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