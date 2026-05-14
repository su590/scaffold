"""
@Date    : 2026/5/6 13:57
@Author  : Chiang
@Desc    : None
"""
import logging
import traceback
from enum import Enum
from typing import Any, TypeVar

import flask
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel
from werkzeug.exceptions import HTTPException


def _to_jsonable(value: Any) -> Any:
    """将类实例转换为可序列化"""
    if isinstance(value, BaseModel):
        return value.model_dump(mode='json')

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {
            key: _to_jsonable(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(item) for item in value]

    return value


class ApiResult(dict):
    """
    If you return a dict or list from a view, it will be converted to a JSON response.
    That means that all the data in the dict or list must be JSON serializable.
    """

    def __init__(self, code: int, data: Any, message: str | None):
        super().__init__(
            code=code,
            data=_to_jsonable(data),
            message=message,
        )

    @classmethod
    def success(cls, data: Any = None, message: str = "成功") -> 'ApiResult':
        return cls(0, data, message)

    @classmethod
    def fail(cls, data: Any = None, message: str = "失败") -> 'ApiResult':
        return cls(1, data, message)


def _handle_validation_error(e: ValidationError):
    """处理 pydantic 参数校验异常"""
    logging.error("参数校验失败: %s", e.errors())
    return ApiResult.fail(
        data=e.errors(),
        message="请求参数错误"
    ), 400


def _handle_http_exception(e: HTTPException):
    """
    处理 flask / Werkzeug HTTP 异常
    如：400 Bad Request 401 Unauthorized 403 Forbidden 404 Not Found 405 Method Not Allow
    """
    logging.error(
        "HTTP异常: code=%s, name=%s, description=%s",
        e.code,
        e.name,
        e.description,
    )

    return ApiResult.fail(
        data=None,
        message=e.description or e.name,
    ), e.code


def _handle_exception(e: Exception):
    """处理兜底异常"""
    logging.exception(f"系统异常{e}\ntraceback={traceback.format_exc()}")
    return ApiResult.fail(
        data=None,
        message=f"系统异常{e}"
    ), 500


def add_error_handler(app: flask.Flask):
    """注册 Flask 全局异常处理器"""
    app.register_error_handler(ValidationError, _handle_validation_error)
    app.register_error_handler(HTTPException, _handle_http_exception)
    app.register_error_handler(Exception, _handle_exception)


class CamelDTO(BaseModel):
    """
    允许小驼峰 > 下划线自动转换
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    def camel(self) -> dict:
        return self.model_dump(by_alias=True)

    def camel_json(self) -> dict:
        return self.model_dump(by_alias=True, mode='json')


T = TypeVar('T', bound=BaseModel)


def parse_body(cls: type[T]) -> T:
    """获取post请求的请求体"""
    body = cls.model_validate(flask.request.get_json())
    logging.info(f"body: {body.model_dump_json()}")
    return body


def parse_params(cls: type[T]) -> T:
    """获取get请求的参数"""
    params = cls.model_validate(flask.request.args.to_dict())
    logging.info(f"params: {params.model_dump_json()}")
    return params
