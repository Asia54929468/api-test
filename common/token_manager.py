from api.client.user_api import ClientUserApi
from common.config import settings
from common.http_client import HttpClient


class ClientTokenManager:
    def __init__(self):
        self._token: str | None = None

    def get_token(self, force_refresh: bool = False) -> str:
        if self._token and not force_refresh:
            return self._token

        client = HttpClient(settings["base_url"])
        user_api = ClientUserApi(client)

        try:
            response = user_api.login(
                username=settings["client_username"],
                password=settings["client_password"],
            )
            response.raise_for_status()

            result = response.json()

            if result.get("code") != 0:
                raise RuntimeError(f"客户端登录失败：{result}")

            token = result["data"]["access_token"]

            if not token:
                raise RuntimeError(
                    f"登录响应中没有 access_token：{result}"
                )

            self._token = token
            return token
        finally:
            client.close()

    def clear_token(self) -> None:
        self._token = None


client_token_manager = ClientTokenManager()