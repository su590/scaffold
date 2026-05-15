# -*- coding: utf-8 -*-  
"""
@Author   : xwq
@Desc     : 统筹消息相关

"""
import requests

from ext.feishu.function.message import compose_text_content, Post


def _send_message(webhook: str, content: dict, msg_type: str) -> requests.Response:
    """
    发送消息
    :param webhook: 添加自定义机器人后的Webhook 地址
    :param content: 消息体
    :param msg_type: 消息类型 - text文本；port富文本
    """
    return requests.post(
        url=webhook,
        headers={'Content-Type': 'application/json'},
        json={
            "msg_type": msg_type,
            "content": content,
        }
    )


def send_text(webhook: str, text: str) -> requests.Response:
    """
    发送文本消息
    :param webhook: 添加自定义机器人后的Webhook 地址
    :param text: 文本内容
    """
    return _send_message(webhook, compose_text_content(text), "text")


def send_post(webhook: str, post: Post) -> requests.Response:
    """
    发送富文本消息
    :param webhook: 添加自定义机器人后的Webhook 地址
    :param post: 富文本
    :return:
    """
    return _send_message(webhook, {'post': post.as_json()}, 'post')
