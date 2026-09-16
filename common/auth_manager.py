from typing import Any
from api.client.user_api import ClientUserApi
from common.config import settings
from common.http_client import HttpClient

class ClientAuthManager:
    def __init__(self):
        self._login_result: dict[str, Any] | None = None

    def _get_login_result(self,force_refresh: bool = False) -> dict[str, Any]:
        """
        登录并缓存完整登录结果。
        """
        if self._login_result and not force_refresh:
            return self._login_result
        client = HttpClient(settings["base_url"])
        user_api = ClientUserApi(client)
        try:
            response = user_api.login(
                username=settings["client_username"],
                password=settings["client_password"],
            )
            response.raise_for_status()
            result = response.json()
            if result.get("code") != 200:
                raise RuntimeError(
                    f"客户端登录失败：{result}"
                )
            self._login_result = result
            return result
        finally:
            client.close()

    def get_token(self,force_refresh: bool = False) -> str:
        result = self._get_login_result(
            force_refresh=force_refresh
        )
        token = result.get("token")
        if not token:
            raise RuntimeError(
                f"登录响应中没有 token：{result}"
            )
        return token

    def get_user_id(self,force_refresh: bool = False) -> int | str:
        result = self._get_login_result(
            force_refresh=force_refresh
        )
        # 确定存在info和userId时可以result[info][userId],使用get可以便于抛出报错
        user_id = result.get("info", {}).get("userId")
        if user_id is None:
            raise RuntimeError(
                f"登录响应中没有 userId：{result}"
            )
        return user_id

    def clear_auth(self) -> None:
        self._login_result = None


client_auth_manager = ClientAuthManager()