from pathlib import Path

import yaml


# 项目根目录
BASE_DIR = Path(__file__).resolve().parents[1]
TESTDATA_DIR = BASE_DIR / "testdata"


def load_yaml(file_path: str) -> dict:
    """
    读取 testdata 目录下的 YAML 文件
    :param file_path: 相对于 testdata 的路径，例如 client/user.yaml
    """
    path = TESTDATA_DIR / file_path

    if not path.exists():
        raise FileNotFoundError(f"测试数据文件不存在：{path}")

    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_data(file_path: str, case_name: str) -> list:
    """
    从 YAML 文件中获取指定测试用例的数据
    """
    data = load_yaml(file_path)
    cases = data.get(case_name)

    if cases is None:
        raise KeyError(
            f"数据文件 {file_path} 中不存在测试用例节点：{case_name}"
        )

    if not isinstance(cases, list):
        raise TypeError(
            f"{file_path} 中的 {case_name} 必须是列表类型"
        )

    return cases