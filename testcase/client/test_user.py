import pytest

from api.client.user_api import ClientUserApi
from common.config import settings
from common.data import load_data
from common.http_client import HttpClient


class TestClientUserApi:
    def test_get_public_key(self):
        client = HttpClient(settings["base_url"])

        try:
            response = ClientUserApi(client).get_public_key()

            assert response.status_code == 200

            result = response.json()
            # print(result)
            assert result["code"] == 200
            assert result["signSk"]
        finally:
            client.close()

    @pytest.mark.parametrize(
        "case",
        load_data(
            "client/user.yaml",
            "test_login",
        ),
        ids=lambda case: case["title"],
    )
    def test_login(self, case: dict):
        request_data = case["request"]
        expected = case["expected"]
        # 优先读取 YAML 中直接配置的值，如果没有，则根据 xxx_key 从 settings 中读取
        username = request_data.get("username")
        password = request_data.get("password")
        if "username_key" in request_data:
            username = settings["client_username"]
        if "password_key" in request_data:
            password = settings["client_password"]

        client = HttpClient(settings["base_url"])
        try:
            response = ClientUserApi(client).login(
                username=username,
                password=password,
            )
            result = response.json()
            # 校验 HTTP 状态码
            assert response.status_code in expected["status_code"]
            # 正常用例：校验 code 等于预期值
            if "code" in expected:
                assert result["code"] == expected["code"]
            # 根据测试数据决定是否校验 token
            if expected.get("token_required"):
                assert result.get("token")
        finally:
            client.close()


    def test_get_user_info_success(self, client_token):
        client = HttpClient(
            settings["base_url"]
        )

        try:
            client.set_token(client_token)
            response = ClientUserApi(client).get_user_info()

            assert response.status_code == 200

            result = response.json()
            # print(result)
            assert result["code"] == 200
        finally:
            client.close()


    # def test_logout_success(self):
    #     client = HttpClient(settings["base_url"])
    #
    #     try:
    #         user_api = ClientUserApi(client)
    #
    #         login_response = user_api.login(
    #             username=settings["client_username"],
    #             password=settings["client_password"],
    #         )
    #         login_response.raise_for_status()
    #
    #         login_result = login_response.json()
    #         assert login_result["code"] == 0
    #
    #         token = login_result["data"]["access_token"]
    #         client.set_token(token)
    #
    #         logout_response = user_api.logout()
    #
    #         assert logout_response.status_code == 200
    #         assert logout_response.json()["code"] == 0
    #     finally:
    #         client.close()