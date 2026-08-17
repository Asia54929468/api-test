from pathlib import Path
import yaml

# 项目根目录及初始化配置
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "config.yaml"


def load_config() -> dict:
    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    # 获取环境及环境下相关配置
    env_name = config["env"]
    env_config = config["environments"][env_name]

    return {
        **env_config,
        **config.get("request", {}),
    }


settings = load_config()