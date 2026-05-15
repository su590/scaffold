# -*- coding: utf-8 -*-
"""
@Author   : xwq & hcq
@Desc     : 统筹卡片相关的组件及其方法

"""

import enum
import json
from typing import Any

import requests


def patch_card(
    tenant_access_token: str,
    message_id: str,
    template_id: str,
    template_version_name: str,
    template_variable: dict[str, str] | None = None,
) -> requests.Response:
    """更新已发送的消息卡片

    参考 https://open.feishu.cn/document/server-docs/im-v1/message-card/patch

    :param tenant_access_token: 应用token
    :param message_id: 目标消息id
    :param template_id: 模板id
    :param template_version_name: 模板版本
    :param template_variable: 模板变量
    :return: 响应
    """
    return requests.patch(
        url=f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {tenant_access_token}",
        },
        json={
            "content": json.dumps(
                {
                    "type": "template",
                    "data": {
                        "template_id": template_id,
                        "template_version_name": template_version_name,
                        "template_variable": template_variable or {},
                    },
                }
            )
        },
    )


class CardType(enum.Enum):
    """卡片类型"""

    CARD_JSON = "card_json"  # 由卡片 JSON 代码构建的卡片
    TEMPLATE = "template"  # 由卡片搭建工具搭建的卡片模板


def create_card_entity(
    tenant_access_token: str,
    card_data: str | dict,
    card_type: str = CardType.TEMPLATE.value,
) -> requests.Response:
    """创建卡片实体

    参考 https://open.feishu.cn/document/cardkit-v1/card/create

    :param tenant_access_token: 应用token
    :param card_data: 卡片数据。如果 card_type 为 "card_json"，应传卡片 JSON 代码（字符串或字典，字典会自动转换为 JSON 字符串）；
                      如果 card_type 为 "template"，应传卡片模板数据 template_id、template_version_name、template_variable
    :param card_type: 卡片类型，可选值："card_json"（由卡片 JSON 代码构建）或 "template"（由卡片搭建工具搭建的卡片模板），默认为 "template"
    :return: 响应，成功时响应体包含 card_id 字段
    """
    # 如果 card_data 是字典，转换为 JSON 字符串
    if isinstance(card_data, dict):
        card_data_str = json.dumps(card_data, ensure_ascii=False)
    else:
        card_data_str = card_data

    return requests.post(
        url="https://open.feishu.cn/open-apis/cardkit/v1/cards",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {tenant_access_token}",
        },
        json={"type": card_type, "data": card_data_str},
    )


class CreateCardEntityResponseShortcut:
    """
    创建卡片实体响应的快捷方式

    :param data: 来自 jsn['data']
    """

    def __init__(self, data: dict[str, Any]):
        self.data = data

    @property
    def card_id(self) -> str:
        """卡片实体 ID"""
        return self.data["card_id"]


def update_card_entity_settings(
    tenant_access_token: str,
    card_id: str,
    settings: str | dict,
    sequence: int,
    uuid: str | None = None,
) -> requests.Response:
    """更新卡片实体配置

    更新指定卡片实体的配置，支持卡片配置 config 字段和卡片跳转链接 card_link 字段。

    参考 https://open.feishu.cn/document/cardkit-v1/card/settings

    :param tenant_access_token: 应用token
    :param card_id: 卡片实体 ID，通过创建卡片实体获取
    :param settings: 卡片配置相关字段转义后的字符串，包括 config 和 card_link 字段。
                     可以是字符串或字典，字典会自动转换为 JSON 字符串。
                     仅支持卡片 JSON 2.0 结构中的对应字段
    :param sequence: 操作卡片的序号，用于保证多次更新的时序性。
                     请确保在通过卡片 OpenAPI 操作同一张卡片时，sequence 的值相较于上一次操作严格递增
    :param uuid: 幂等 ID，可通过传入唯一的 UUID 以保证相同批次的操作只进行一次，可选
    :return: 响应
    """
    # 如果 settings 是字典，转换为 JSON 字符串
    if isinstance(settings, dict):
        settings_str = json.dumps(settings, ensure_ascii=False)
    else:
        settings_str = settings

    request_body: dict[str, Any] = {"settings": settings_str, "sequence": sequence}
    if uuid is not None:
        request_body["uuid"] = uuid

    return requests.patch(
        url=f"https://open.feishu.cn/open-apis/cardkit/v1/cards/{card_id}/settings",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {tenant_access_token}",
        },
        json=request_body,
    )


def update_card_element_content(
    tenant_access_token: str,
    card_id: str,
    element_id: str,
    content: str,
    sequence: int,
    uuid: str | None = None,
) -> requests.Response:
    """流式更新文本

    对卡片中的普通文本元素（tag 为 plain_text 的元素）或富文本组件（tag 为 markdown 的组件）
    传入全量文本内容，以实现"打字机"式的文字输出效果。

    参考 https://open.feishu.cn/document/cardkit-v1/card-element/content

    :param tenant_access_token: 应用token
    :param card_id: 卡片实体 ID，通过创建卡片实体获取
    :param element_id: 卡片实体中，普通文本元素或富文本组件的 ID。
                       对应卡片 JSON 中的 element_id 属性或搭建工具中的组件 ID 属性，由开发者自定义。
                       仅支持卡片 JSON 2.0 结构或卡片搭建工具搭建的新版卡片。
                       对于搭建工具中的卡片，此处仅支持传入富文本组件的组件 ID
    :param content: 新的全量文本内容。
                    若旧文本为传入的新文本的前缀子串，新增文本将在旧文本末尾继续以打字机效果输出；
                    若新旧文本前缀不同，全量文本将直接上屏输出，无打字机效果。
                    注意：若 content 中含有代码块，需将代码块前后的空格去掉，否则可能导致代码渲染失败
    :param sequence: 操作卡片的序号，用于保证多次更新的时序性。
                     请确保在通过卡片 OpenAPI 操作同一张卡片时，sequence 的值相较于上一次操作严格递增
    :param uuid: 幂等 ID，可通过传入唯一的 UUID 以保证相同批次的操作只进行一次，可选
    :return: 响应
    """
    request_body: dict[str, Any] = {"content": content, "sequence": sequence}
    if uuid is not None:
        request_body["uuid"] = uuid

    return requests.put(
        url=f"https://open.feishu.cn/open-apis/cardkit/v1/cards/{card_id}/elements/{element_id}/content",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {tenant_access_token}",
        },
        json=request_body,
    )
