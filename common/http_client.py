import requests
from common.config import settings


class HttpClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        # 声明请求体和客户端期望接受为JSON格式
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        if token:
            self.set_token(token)

    def set_token(self, token: str) -> None:
        self.session.headers.update({
            "Authorization": f"{token}"
        })

    # 拼接url并请求接口
    def request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"

        response = self.session.request(
            method=method,
            url=url,
            timeout=settings.get("timeout", 10),
            verify=settings.get("verify_ssl", True),
            **kwargs,
        )

        return response

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def close(self) -> None:
        self.session.close()