from unittest import case

import pytest
import time
from api.client.user_api import ClientUserApi
from common.config import settings
from common.data import load_data
from common.http_client import HttpClient
from common.http_logging import log_http_response


class TestClientUserApi:
    def test_get_public_key(self, log_http):
        client = HttpClient(settings["base_url"])

        try:
            response = ClientUserApi(client).get_public_key()
            result = response.json()

            log_http(
                response,
                title="获取公钥",
            )

            assert response.status_code == 200
            assert result["code"] == 200
            assert result["signSk"]
        finally:
            client.close()

    def test_get_account_setting(self, log_http):
        client = HttpClient(settings["base_url"])

        try:
            response = ClientUserApi(client).get_account_setting()
            result = response.json()

            log_http(
                response,
                title="获取账号配置成功",
            )

            assert response.status_code == 200
            assert result["code"] == 200

            assert isinstance(result["info"], dict)
            assert isinstance(
                result["info"]["loginType"],
                list,
            )
            assert isinstance(
                result["info"]["checkLoginType"],
                list,
            )
            assert isinstance(
                result["info"]["passwordRule"],
                list,
            )

            assert isinstance(
                result["passwordRules"],
                dict,
            )
            assert isinstance(result["larkLogin"], dict)
            assert isinstance(result["weComLogin"], dict)
            assert isinstance(result["debuglog"], dict)
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
    def test_login(self, case: dict, log_http):
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

            log_http(
                response,
                title=case["title"],
            )

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

    def test_logout(self, client_token, log_http):
        client = HttpClient(settings["base_url"])

        try:
            client.set_token(client_token)
            response = ClientUserApi(client).logout()
            result = response.json()

            log_http(
                response,
                title="退出登录成功",
            )

            assert response.status_code == 200
            assert result["code"] == 200
            if "message" in result:
                assert isinstance(result["message"], str)
        finally:
            client.close()

    def test_get_user_info(self, client_token, client_user_id, log_http):
        client = HttpClient(settings["base_url"])

        try:
            client.set_token(client_token)
            response = ClientUserApi(client).get_user_info(user_id=client_user_id)
            result = response.json()

            log_http(
                response,
                title="获取用户信息成功"
            )

            assert response.status_code == 200
            assert result["code"] == 200
        finally:
            client.close()

    def test_get_user_organizations(self, client_token, log_http):
        client = HttpClient(settings["base_url"])

        try:
            client.set_token(client_token)
            response = ClientUserApi(client).get_user_organizations()
            result = response.json()

            log_http(
                response,
                title="获取当前用户的组织列表成功"
            )

            assert response.status_code == 200
            assert result["code"] == 200
            assert "organizations" in result
            assert isinstance(
                result["organizations"],
                list,
            )
            assert len(result["organizations"]) == 1
        finally:
            client.close()

    @pytest.mark.parametrize(
        "case",
        load_data(
            "client/user.yaml",
            "test_change_password",
        ),
        ids=lambda case: case["title"],
    )
    def test_change_password(self, case: dict, client_token, log_http):
        request_data = case["request"]
        expected = case["expected"]

        # 优先读取 YAML 中直接配置的值，如果没有，则根据 xxx_key 从 settings 中读取
        password = request_data.get("password")
        new_password = request_data.get("new_password")
        if "password_key" in request_data:
            password = settings["client_password"]

        client = HttpClient(settings["base_url"])
        password_changed = False

        try:
            client.set_token(client_token)
            response = ClientUserApi(client).change_password(
                password=password,
                new_password=new_password,
            )
            result = response.json()

            log_http(
                response,
                title=case["title"],
            )

            # 接口实际修改成功后，需要在 finally 中恢复密码
            password_changed = (
                    expected.get("restore_password", False)
                    and response.status_code
                    in expected["status_code"]
                    and result.get("code")
                    == expected.get("code")
            )

            # 校验 HTTP 状态码
            assert (
                    response.status_code
                    in expected["status_code"]
            )

            # 根据测试数据校验业务码
            if "code" in expected:
                assert result["code"] == expected["code"]
        finally:
            client.close()

            if password_changed:
                restore_client = HttpClient(settings["base_url"])

                try:
                    # 修改密码后原 Token 可能已经失效，使用新密码重新登录获取 Token
                    login_response = ClientUserApi(restore_client).login(
                        username=settings["client_username"],
                        password=new_password,
                    )
                    login_result = login_response.json()

                    log_http(
                        login_response,
                        title="新密码登录成功",
                    )

                    assert login_response.status_code == 200
                    assert login_result["code"] == 200
                    assert login_result.get("token")

                    time.sleep(1)

                    restore_client.set_token(
                        login_result["token"]
                    )

                    # 将密码恢复为配置中的原密码
                    restore_response = ClientUserApi(restore_client).change_password(
                        password=new_password,
                        new_password=password,
                    )
                    restore_result = (restore_response.json())

                    log_http(
                        restore_response,
                        title="恢复原密码",
                    )

                    assert (restore_response.status_code == 200)
                    assert restore_result["code"] == 200
                finally:
                    restore_client.close()