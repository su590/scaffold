"""
@Author   : hcq
@Time     : 2025/11/7 14:37
@Desc     : redis装饰器
@warning  : 整体的key必须以:来进行分隔
"""
from src.main.constance import RDS
from src.main.redis import client

_PREFIX = f"{RDS}:cache"


def _key(key: str) -> str:
    if not key:
        return _PREFIX
    return f"{_PREFIX}:{key}"


def set_cache_nx(key: str, value: str, expire: int) -> bool:
    """
    SET key NX EX：仅当 key 不存在时写入。
    :return: True 表示本次写入成功（首次），False 表示 key 已存在。
    """
    return bool(client.set(_key(key), value, nx=True, ex=expire))


def set_cache(key: str, value: str, expire: int | None = None) -> None:
    """
    设置缓存
    :param key: 缓存的键
    :param value: 缓存的值
    :param expire: 有效期 无 则永久有效
    :return:
    """
    client.set(_key(key), value, expire)


def get_cache(key: str) -> str | None:
    """
    获取缓存
    :param key: 缓存键
    :return: 缓存的值
    """
    return client.get(_key(key))


def delete_cache(key: str) -> None:
    """
    删除缓存内容
    :param key: 缓存键
    :return:
    """
    client.delete(_key(key))


def delete_cache_by_prefix(prefix: str) -> int:
    """
    根据前缀删除缓存
    :param prefix: 缓存的前缀
    :return: 删除的键数量
    """
    cursor = 0
    deleted_count = 0
    real_prefix = _key(prefix)
    while True:
        cursor, keys = client.scan(
            cursor=cursor,
            match=f"{real_prefix}:*",
            count=1000,
        )
        if keys:
            # unlink进行异步删除 不会阻塞主线程
            deleted_count += client.unlink(*keys)
        if cursor == 0:
            break
    return deleted_count


def get_cached_suffix(prefix: str) -> list[str]:
    """
    获取缓存的后缀
    :param prefix: 缓存键的前缀，形如 a, a:b
    :return: 缓存键的后缀
    """
    cursor = 0
    accords = []
    real_prefix = _key(prefix)
    while True:
        cursor, keys = client.scan(
            cursor=cursor,
            match=f"{real_prefix}:*",
            count=1000,
        )
        if keys:
            accords.extend(keys)
        if cursor == 0:
            break
    return [accord.split(f"{real_prefix}:")[-1] for accord in accords]
