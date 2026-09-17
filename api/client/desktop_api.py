import requests
from common.http_client import HttpClient


class ClientDesktopApi:
    DESKTOP_SERVERS_PATH = "/api/v1/desktop/servers"
    DESKTOP_SERVER_DETAIL_PATH = "/api/v1/desktop/servers/{id}"

    def __init__(self, client: HttpClient):
        self.client = client

    def get_desktop_servers(self) -> requests.Response:
        """
        获取桌面服务器列表。
        """
        return self.client.get(self.DESKTOP_SERVERS_PATH)

    def get_desktop_server_detail(self, desktop_id: int | str) -> requests.Response:
        """
        获取桌面详情。
        """
        return self.client.get(
            self.DESKTOP_SERVER_DETAIL_PATH,
            path_params={"id": desktop_id},
        )