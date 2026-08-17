from typing import Any
import requests
from common.http_client import HttpClient
from common.crypto import encrypt

class ClientUserApi:
    NACL_PUBLIC_KEY_PATH = "/api/v1/common/nacl-public-key"
    LOGIN_PATH = "/api/v1/common/login"


    def __init__(self, client: HttpClient):
        self.client = client
    def get_public_key(self) -> requests.Response:
        return self.client.post(self.NACL_PUBLIC_KEY_PATH)
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
            if public_key_result.get("code") != 0:
                raise RuntimeError(
                    f"获取公钥失败：{public_key_result}"
                )
            public_key = public_key_result["data"]["signSk"]
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