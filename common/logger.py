import logging
import logging.config
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_CONFIG_PATH = PROJECT_ROOT / "config" / "logging.yaml"
LOG_DIR = PROJECT_ROOT / "logs"


def setup_logging(
    write_to_file: bool = True,
) -> Optional[Path]:
    """
    初始化日志配置。

    Args:
        write_to_file:
            True：
                生成带时间戳的日志文件，保持原有功能。
            False：
                不创建日志目录和日志文件，
                日志仅交给pytest捕获。

    Returns:
        write_to_file=True时，返回本次运行的日志文件路径；
        write_to_file=False时，返回None。
    """

    if not LOG_CONFIG_PATH.is_file():
        raise FileNotFoundError(
            f"日志配置文件不存在：{LOG_CONFIG_PATH}"
        )

    with LOG_CONFIG_PATH.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(
            f"日志配置文件内容无效：{LOG_CONFIG_PATH}"
        )

    if write_to_file:
        log_file_path = _enable_file_logging(config)
    else:
        log_file_path = None
        _disable_output_handlers(config)

    logging.config.dictConfig(config)

    return log_file_path


def _enable_file_logging(config: dict) -> Path:
    """
    启用文件日志。

    保持原有功能：每次启动测试时生成一个
    带时间戳的日志文件。
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    handlers = config.get("handlers", {})
    file_handler = handlers.get("file")

    if not isinstance(file_handler, dict):
        raise KeyError(
            "logging.yaml中不存在handlers.file配置"
        )

    configured_filename = file_handler.get("filename")

    if not configured_filename:
        raise KeyError(
            "logging.yaml中不存在"
            "handlers.file.filename配置"
        )

    # 获取YAML中配置的基础文件名，
    # 例如logs/api_test.log。
    configured_path = Path(configured_filename)

    # 生成本次测试运行的时间戳。
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    # api_test.log
    # 转换为api_test_20260905_134558.log。
    log_filename = (
        f"{configured_path.stem}_{timestamp}"
        f"{configured_path.suffix or '.log'}"
    )

    log_file_path = LOG_DIR / log_filename

    config["handlers"]["file"]["filename"] = str(
        log_file_path
    )

    return log_file_path


def _disable_output_handlers(config: dict) -> None:
    """
    关闭文件和控制台输出。

    日志不写入日志文件，也不通过StreamHandler写入stdout，
    而是向上传播并交给pytest日志插件捕获。
    """

    handlers = config.setdefault("handlers", {})
    loggers = config.setdefault("loggers", {})

    # 从所有Logger中移除file和console Handler引用。
    for logger_name, logger_config in loggers.items():
        if not isinstance(logger_config, dict):
            continue

        configured_handlers = logger_config.get(
            "handlers",
            [],
        )

        logger_config["handlers"] = [
            handler_name
            for handler_name in configured_handlers
            if handler_name not in {"file", "console"}
        ]

        # 项目日志需要向上传播，
        # 才能被pytest的日志捕获器捕获。
        if (
            logger_name == "api_test"
            or logger_name.startswith("api_test.")
        ):
            logger_config["propagate"] = True

    # 从root Logger中移除file和console Handler引用，
    # 避免创建日志文件或产生Captured stdout。
    root_config = config.get("root")

    if isinstance(root_config, dict):
        root_handlers = root_config.get("handlers", [])

        root_config["handlers"] = [
            handler_name
            for handler_name in root_handlers
            if handler_name not in {"file", "console"}
        ]

    # 删除Handler定义。
    #
    # 不能只删除Logger中的引用，因为dictConfig可能仍会
    # 初始化handlers.file，从而创建空日志文件。
    handlers.pop("file", None)
    handlers.pop("console", None)


def get_logger(
    name: Optional[str] = None,
) -> logging.Logger:
    """
    获取项目Logger。

    get_logger()              -> api_test
    get_logger("http")        -> api_test.http
    get_logger("http_client") -> api_test.http_client
    """

    logger_name = (
        "api_test" if not name else f"api_test.{name}"
    )

    return logging.getLogger(logger_name)