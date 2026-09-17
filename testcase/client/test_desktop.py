from api.client.desktop_api import ClientDesktopApi
from common.config import settings
from common.http_client import HttpClient


class TestClientDesktopApi:
    def test_get_desktop_servers(self, client_token, log_http):
        client = HttpClient(settings["base_url"])

        try:
            client.set_token(client_token)
            response = ClientDesktopApi(client).get_desktop_servers()
            result = response.json()

            log_http(
                response,
                title="获取桌面服务器列表成功",
                details=True
            )

            assert response.status_code == 200
            assert result["code"] == 200

            assert "list" in result
            assert isinstance(result["list"], list)
            # 若list非空则获取list第一个元素
            if result["list"]:
                desktop = result["list"][0]
                assert desktop.get("desktopId")
                assert desktop.get("name")
                assert "status" in desktop
                assert "isOnline" in desktop
                assert isinstance(
                    desktop["isOnline"],
                    bool,
                )
                if desktop["isOnline"]:
                    assert "userInfo" in desktop
        finally:
            client.close()

    def test_get_desktop_server_detail(self, client_token, client_desktop_id, log_http):
        client = HttpClient(settings["base_url"])

        try:
            client.set_token(client_token)
            response = ClientDesktopApi(client).get_desktop_server_detail(
                desktop_id=client_desktop_id,
            )
            result = response.json()

            log_http(
                response,
                title="获取桌面详情成功",
                details=True
            )

            assert response.status_code == 200
            assert result["code"] == 200
            assert isinstance(result["detail"], dict)
            assert (
                str(result["detail"]["desktopId"]) == str(client_desktop_id)
            )
        finally:
            client.close()