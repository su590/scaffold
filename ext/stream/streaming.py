"""
@Date     : 2026-04-29
@Author   : Chiang
@Desc     : 长耗时同步接口的 NDJSON 流式保活装饰器, 用于绕过网关 idle 超时

协议:
    心跳: {"_t":"hb"}\n
    结果: {"_t":"r","payload":<view 原返回值>}\n
    异常: {"_t":"e","message":"..."}\n

被装饰函数的返回值需可 json 序列化, dict / pydantic.BaseModel / ApiResult 均可
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from functools import wraps
from typing import Any, Callable

from flask import Response, copy_current_request_context

_HB_LINE = json.dumps({"_t": "hb"}, ensure_ascii=False) + "\n"
_executor = ThreadPoolExecutor(max_workers=16, thread_name_prefix="stream-keepalive")


def _serialize(result: Any) -> Any:
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    return result


def _err_line(message: str) -> str:
    return json.dumps({"_t": "e", "message": message}, ensure_ascii=False) + "\n"


def stream_keepalive(interval: float = 30.0, timeout: float = 180.0) -> Callable:
    """
    把同步阻塞的 view function 转成 NDJSON 流式响应

    :param interval: 心跳间隔秒数, 默认 30
    :param timeout: 任务最大等待秒数, 超过则结束流并返回错误, 默认 180
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Response]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Response:
            ctx_func = copy_current_request_context(func)
            future = _executor.submit(ctx_func, *args, **kwargs)

            def generate():
                start = time.monotonic()
                while True:
                    remaining = timeout - (time.monotonic() - start)
                    if remaining <= 0:
                        # Python 线程不可强制中断, 子线程会继续执行直到 LangChain 返回, 此处仅释放客户端连接
                        logging.warning(
                            f"stream_keepalive task exceeded timeout={timeout}s, abandoning future"
                        )
                        yield _err_line(f"任务超时 ({timeout}s)")
                        return
                    try:
                        result = future.result(timeout=min(interval, remaining))
                    except FutureTimeout:
                        yield _HB_LINE
                        continue
                    except Exception as e:
                        logging.error("stream_keepalive task error", exc_info=True)
                        yield _err_line(str(e))
                        return
                    yield json.dumps(
                        {"_t": "r", "payload": _serialize(result)}, ensure_ascii=False
                    ) + "\n"
                    return

            return Response(generate(), mimetype="application/x-ndjson")

        return wrapper

    return decorator
