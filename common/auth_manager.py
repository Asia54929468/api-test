from typing import Any

from api.client.desktop_api import ClientDesktopApi
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


class ClientDesktopManager:
    def __init__(self,auth_manager: ClientAuthManager):
        self.auth_manager = auth_manager
        self._desktop_id: int | str | None = None

    def get_desktop_id(self,force_refresh: bool = False) -> int | str:
        """
        获取并缓存当前用户桌面列表中的第一个桌面 ID。
        """
        if self._desktop_id is not None and not force_refresh:
            return self._desktop_id
        client = HttpClient(settings["base_url"])
        desktop_api = ClientDesktopApi(client)
        try:
            client.set_token(
                self.auth_manager.get_token()
            )
            response = desktop_api.get_desktop_servers()
            response.raise_for_status()
            result = response.json()
            if result.get("code") != 200:
                raise RuntimeError(
                    f"获取桌面列表失败：{result}"
                )
            desktop_list = result.get("list", [])
            if not desktop_list:
                raise RuntimeError(
                    "当前用户没有可用的桌面"
                )
            desktop_id = desktop_list[0].get("desktopId")
            if desktop_id is None:
                raise RuntimeError(
                    f"桌面数据中没有 desktopId："
                    f"{desktop_list[0]}"
                )
            self._desktop_id = desktop_id
            return desktop_id
        finally:
            client.close()
    def clear_desktop(self) -> None:
        self._desktop_id = None

client_auth_manager = ClientAuthManager()
client_desktop_manager = ClientDesktopManager(client_auth_manager)