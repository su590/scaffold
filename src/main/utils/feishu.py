"""
@Date    : 2026/5/15 16:24
@Author  : Chiang
@Desc    : None
"""
import logging
import threading
import time
import traceback

import requests

from ext.feishu.function.token import get_tenant_access_token
from src.main.config import get_config
from src.main.redis.cache import get_cache, set_cache

_APP_ID = get_config("feishu", "app_id")
_APP_SECRET = get_config("feishu", "app_secret")
_KEY_PREFIX = "feishu"
_TOKEN_KEY = f"{_KEY_PREFIX}:token"
_token_lock = threading.Lock()


def load_token() -> str | None:
    """
    从缓存加载tenant_access_token
    :return:
    """
    token = get_cache(_TOKEN_KEY)
    if token:
        return token

    with _token_lock:
        token = get_cache(_TOKEN_KEY)
        if token:
            return token

        for i in range(3):
            if i != 0:
                gap = 3 ** i
                logging.warning(f"前{i}次获取token失败，等待{gap}秒重试...")
                time.sleep(gap)

            try:
                response = get_tenant_access_token(_APP_ID, _APP_SECRET)
            except Exception:
                logging.error(f"获取token失败: {traceback.format_exc()}")
                continue

            try:
                response.raise_for_status()
            except requests.HTTPError:
                logging.error(f"获取token失败: {response.status_code}, {response.text}")
                continue

            jsn = response.json()
            expire: int = jsn["expire"]
            tenant_access_token: str = jsn["tenant_access_token"]
            set_cache(_TOKEN_KEY, tenant_access_token, expire)
            return tenant_access_token

    return None
