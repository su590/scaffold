"""
@Date    : 2026/5/15 15:11
@Author  : Chiang
@Desc    : None
"""
import redis

from src.main.config import get_config


def _generate_client():
    conf = get_config("redis")
    pool = redis.ConnectionPool(
        # 基础配置
        host=conf["host"],
        port=conf["port"],
        db=conf["db"],
        password=conf["password"],
        # 连接行为优化
        socket_connect_timeout=3,  # 连接超时
        socket_timeout=10,  # 读写超时（含重试时间）
        retry_on_timeout=True,  # 连接超时后自动重试
        max_connections=200,  # 最大连接数（根据负载调整）
        # 资源管理
        socket_keepalive=True,  # 启用TCP保活机制，防止连接因闲置断开
        health_check_interval=15,  # 健康检查间隔
        # max_idle_time=60,  # 连接最大空闲时间
        # idle_check_interval=30,  # 空闲连接检查频率
        # 自动解码
        decode_responses=True,
        encoding="utf-8",
        encoding_errors="strict",
    )
    return redis.Redis(
        connection_pool=pool,
    )


client = _generate_client()
