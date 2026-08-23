import logging
import logging.config
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_CONFIG_PATH = PROJECT_ROOT / "config" / "logging.yaml"
LOG_DIR = PROJECT_ROOT / "logs"


def setup_logging():
    """初始化日志配置。"""

    # 日志目录不存在时自动创建
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with open(LOG_CONFIG_PATH, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    # 将YAML中的相对日志路径转换为绝对路径，
    # 避免从不同目录执行pytest时日志位置发生变化
    filename = config["handlers"]["file"]["filename"]
    config["handlers"]["file"]["filename"] = str(
        PROJECT_ROOT / filename
    )

    logging.config.dictConfig(config)


def get_logger(name=None):
    """
    获取项目Logger。

    例如：
        get_logger("http_client")
    最终Logger名称为：
        api_test.http_client
    """
    logger_name = "api_test" if not name else f"api_test.{name}"
    return logging.getLogger(logger_name)