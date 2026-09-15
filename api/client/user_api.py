from typing import Any
import requests
from common.http_client import HttpClient
from common.crypto import encrypt

class ClientUserApi:
    NACL_PUBLIC_KEY_PATH = "/api/v1/common/nacl-public-key"
    ACCOUNT_SETTING_PATH = "/api/v1/common/account-setting"
    LOGIN_PATH = "/api/v1/common/login"
    LOGOUT_PATH = "/api/v1/common/logout"
    USER_INFO_PATH = "/api/v1/user/lists/{id}"
    USER_ORGANIZATIONS_PATH = "/api/v1/user/organizations"
    CHANGE_PASSWORD_PATH = "/api/v1/common/change-password"

    def __init__(self, client: HttpClient):
        self.client = client
    def get_public_key(self) -> requests.Response:
        """
        获取公钥。
        """
        return self.client.post(self.NACL_PUBLIC_KEY_PATH)
    def get_account_setting(self) -> requests.Response:
        """
        获取账号配置。
        """
        return self.client.get(self.ACCOUNT_SETTING_PATH)
    def login(
        self,
        username: str,
        password: str,
        *,
        need_encrypt: bool = True,
        mode: str = "password",
        sn: str | None = None,
        **extra_fields: Any,
    ) -> requests.Response:
        """
        客户端登录。
        默认先请求公钥，再使用公钥加密密码。
        extra_fields 可传验证码、设备编号等额外登录参数。
        """
        login_password = password
        if need_encrypt:
            public_key_response = self.get_public_key()
            public_key_response.raise_for_status()
            public_key_result = public_key_response.json()
            if public_key_result.get("code") != 200:
                raise RuntimeError(
                    f"获取公钥失败：{public_key_result}"
                )
            public_key = public_key_result["signSk"]
            login_password = encrypt(password, public_key)
        payload = {
            "username": username,
            "password": login_password,
            "mode": mode,
        }
        if sn is not None:
            payload["sn"] = sn
        payload.update(extra_fields)

        return self.client.post(
            self.LOGIN_PATH,
            json=payload,
        )
    def logout(self) -> requests.Response:
        """
        退出当前登录用户。
        """
        return self.client.post(self.LOGOUT_PATH)
    def get_user_info(self) -> requests.Response:
        """
        获取当前登录用户信息。
        """
        return self.client.get(self.USER_INFO_PATH, path_params = {"id":4})
    def get_user_organizations(self) -> requests.Response:
        """
        获取当前用户的组织列表。
        """
        return self.client.get(self.USER_ORGANIZATIONS_PATH)

    def change_password(
            self,
            password: str,
            new_password: str,
    ) -> requests.Response:
        """
        修改当前登录用户密码。
        """
        payload = {
            "password": password,
            "newPassword": new_password,
        }

        return self.client.post(
            self.CHANGE_PASSWORD_PATH,
            json=payload,
        )