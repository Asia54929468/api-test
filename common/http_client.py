import re
from urllib.parse import quote
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

    @staticmethod
    def _replace_path_params(path: str, path_params: dict | None = None) -> str:
        """
        替换 URL 中的路径参数。
        示例：
        path = "/api/v1/users/{id}/reset-password"
        path_params = {"id": 10001}
        返回：
        "/api/v1/users/10001/reset-password"
        """
        path_params = path_params or {}
        # 查找路径中所有的占位符，例如 {id}、{user_id}
        placeholders = re.findall(r"\{([^{}]+)\}", path)
        # 检查是否缺少路径参数
        missing_params = [
            name
            for name in placeholders
            if name not in path_params
        ]
        if missing_params:
            raise ValueError(
                f"URL 路径参数缺失：{missing_params}，请求路径：{path}"
            )
        # 替换路径参数
        for name in placeholders:
            value = path_params[name]
            if value is None:
                raise ValueError(
                    f"URL 路径参数 '{name}' 不能为 None"
                )
            # 对空格、中文、斜杠等特殊字符进行编码
            encoded_value = quote(str(value), safe="")
            path = path.replace(
                f"{{{name}}}",
                encoded_value
            )
        return path

    # 拼接url并请求接口
    def request(self, method: str, path: str, path_params: dict | None = None, **kwargs):
        path = self._replace_path_params(
            path=path,
            path_params=path_params
        )
        url = f"{self.base_url}/{path.lstrip('/')}"

        response = self.session.request(
            method=method,
            url=url,
            timeout=settings.get("timeout", 10),
            verify=settings.get("verify_ssl", True),
            **kwargs,
        )

        return response

    def get(self, path: str, path_params: dict | None = None, **kwargs):
        return self.request("GET", path, path_params = path_params, **kwargs)

    def post(self, path: str, path_params: dict | None = None, **kwargs):
        return self.request("POST", path, path_params = path_params, **kwargs)

    def put(self, path: str, path_params: dict | None = None, **kwargs):
        return self.request("PUT", path, path_params = path_params, **kwargs)

    def delete(self, path: str, path_params: dict | None = None, **kwargs):
        return self.request("DELETE", path, path_params = path_params, **kwargs)

    def close(self) -> None:
        self.session.close()