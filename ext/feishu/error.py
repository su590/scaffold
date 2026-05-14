"""
@Author   : hcq
@Time     : 2025/11/7 13:50
@Desc     : 统筹飞书错误

"""


class FeishuError(Exception):
    _msg = "飞书错误"


class RetryTooMuch(FeishuError):
    _msg = "飞书重试次数过多"
