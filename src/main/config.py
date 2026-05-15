"""
@Date    : 2026/5/15 14:15
@Author  : Chiang
@Desc    : 配置文件
"""
import os
from typing import Any

import yaml

from src.main.constance import ENV, ROOT_PATH


def is_env_prod() -> bool:
    """
    判断当前环境是不是生产环境
    :return:
    """
    try:
        return os.environ[ENV] == 'prod'
    except KeyError:
        return False


_CONFIG_PATH = ROOT_PATH / 'src' / 'resources' / ('config.yml' if is_env_prod() else 'config_dev.yml')


def _load_config() -> dict:
    content = _CONFIG_PATH.read_text(encoding='utf-8')
    return yaml.safe_load(content)


_CONFIG_CACHE: dict = _load_config()


def get_config(*keys: str) -> Any:
    """
    获取配置文件的内容
    :param keys: 配置文件当中的key，按顺序展示
    :return:
    """
    result = _CONFIG_CACHE
    for key in keys:
        result = result[key]
    return result
