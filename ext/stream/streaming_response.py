"""
@Date     : 2026-04-29
@Author   : Chiang
@Desc     : stream_keepalive 接口的客户端调用辅助
"""
import json
import requests


def stream_request(method: str, url: str, **kwargs) -> dict:
    """
    调用 stream_keepalive 装饰的接口, 自动过滤心跳, 返回最终 payload (相当于 resp.json())
    用法与 requests.request 一致, stream 参数会被强制设为 True

    :param method: GET / POST / ...
    :param url: 接口地址
    :param kwargs: 其他 requests 参数, 注意 timeout 建议传 (connect, read), 且 read >= 心跳间隔的 2 倍
    :return: 服务端 view function 的原返回值 (一般是 ApiResult dict)
    """
    kwargs["stream"] = True
    with requests.request(method, url, **kwargs) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            msg = json.loads(line)
            t = msg.get("_t")
            if t == "hb":
                continue
            if t == "e":
                raise RuntimeError(f"AI 服务异常: {msg.get('message')}")
            if t == "r":
                return msg["payload"]
        raise RuntimeError("AI 服务未返回结果")


def stream_post(url: str, **kwargs) -> dict:
    return stream_request("POST", url, **kwargs)


def stream_get(url: str, **kwargs) -> dict:
    return stream_request("GET", url, **kwargs)