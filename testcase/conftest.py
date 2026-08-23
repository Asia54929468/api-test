import pytest

from api.client.user_api import ClientUserApi
from common.config import settings
from common.http_client import HttpClient
from common.token_manager import client_token_manager

from common.logging import setup_logging, get_logger


# def pytest_configure(config):
#     """pytest启动时执行一次。"""
#     setup_logging()
#
#     logger = get_logger("pytest")
#     logger.info("=" * 60)
#     logger.info("pytest接口自动化测试开始")
#     logger.info("=" * 60)
#
#
# def pytest_unconfigure(config):
#     """pytest执行结束时调用。"""
#     logger = get_logger("pytest")
#     logger.info("=" * 60)
#     logger.info("pytest接口自动化测试结束")
#     logger.info("=" * 60)


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