import pytest

from api.client.user_api import ClientUserApi
from common.config import settings
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

    def test_login_success(self):
        client = HttpClient(settings["base_url"])

        try:
            response = ClientUserApi(client).login(
                username=settings["client_username"],
                password=settings["client_password"],
            )

            assert response.status_code == 200

            result = response.json()
            # print(result)
            assert result["code"] == 200
            assert result["token"]
        finally:
            client.close()

    @pytest.mark.parametrize(
        "username,password",
        [
            ("invalid-user", "invalid-password"),
            ("", ""),
        ],
    )
    def test_login_failed(self, username: str, password: str):
        client = HttpClient(settings["base_url"])

        try:
            response = ClientUserApi(client).login(
                username=username,
                password=password,
            )

            result = response.json()
            # print(result)
            assert response.status_code in (200, 400, 401, 500)
            assert result["code"] != 200
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