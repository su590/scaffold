# -*- coding: utf-8 -*-
"""
@Author   : hcq
@Desc     : 流式更新卡片类，封装卡片流式更新的完整流程

使用示例：
    card = StreamingCard(tenant_access_token=load_token())
    card.create_and_send(
        receive_id="user_id",
        template_id="AAqhF5MGpzveE",
        template_version_name="1.0.5",
        template_variable={"content": "初始内容"}
    )

    # 流式更新文本
    card.update_text("element_post_content", "第一部分文本")
    card.update_text("element_post_content", "第一部分文本第二部分文本")

    # 关闭流式更新模式 (！！！在关闭流式更新之后才能去处理卡片回调！！！)
    card.disable_streaming_mode()
"""

import uuid
from typing import Any

from ext.feishu.card import (
    CardType,
    CreateCardEntityResponseShortcut,
    create_card_entity,
    update_card_element_content,
    update_card_entity_settings,
)
from ext.feishu.message import ReceiveIdType, send_interactive_by_card_id
from ext.feishu.retry import retry_feishu_api


class StreamingCard:
    """流式更新卡片类

    用于管理卡片实体的创建、发送、流式更新文本和配置更新等操作。
    使用 template 方式创建卡片，创建的卡片默认已开启流式更新模式，无需额外配置。
    自动管理 sequence 的递增，简化流式更新流程。
    """

    def __init__(self, tenant_access_token: str):
        """初始化流式更新卡片

        :param tenant_access_token: 应用token
        """
        self.tenant_access_token = tenant_access_token
        self.card_id: str | None = None
        self.sequence = 1

    def _next_sequence(self) -> int:
        """获取下一个序号并递增"""
        current = self.sequence
        self.sequence += 1
        return current

    def _create_card_entity_with_streaming(
        self,
        template_id: str,
        template_version_name: str,
        template_variable: dict[str, Any],
    ) -> str:
        """创建开启流式更新模式的卡片实体

        使用 template 方式创建的卡片默认已开启流式更新模式，无需额外配置。

        :param template_id: 卡片模板 ID
        :param template_version_name: 模板版本号，如 "1.0.5"
        :param template_variable: 模板变量字典，如 {"content": "文本内容"}
        :return: 卡片实体 ID
        """
        # 构建模板数据
        template_data = {
            "template_id": template_id,
            "template_version_name": template_version_name,
            "template_variable": template_variable,
        }

        # 创建卡片实体（使用 template 类型）
        result = retry_feishu_api(
            api=create_card_entity,
            args=[
                self.tenant_access_token,
                template_data,
                CardType.TEMPLATE.value,
            ],
        )

        self.card_id = CreateCardEntityResponseShortcut(result["data"]).card_id
        return self.card_id

    def _send_card(
        self,
        receive_id: str,
        receive_id_type: str = ReceiveIdType.USER_ID.value,
    ) -> dict[str, Any]:
        """发送卡片实体

        :param receive_id: 目标 ID
        :param receive_id_type: 目标 ID 类型，默认为 user_id
        :return: 响应数据（字典格式）
        """
        if not self.card_id:
            raise ValueError("卡片实体 ID 不存在，请先创建卡片实体")

        return retry_feishu_api(
            api=send_interactive_by_card_id,
            args=[
                receive_id,
                self.card_id,
                self.tenant_access_token,
                receive_id_type,
            ],
        )

    def create_and_send(
        self,
        receive_id: str,
        template_id: str,
        template_version_name: str,
        template_variable: dict[str, Any],
        receive_id_type: str = ReceiveIdType.USER_ID.value,
    ) -> dict[str, Any]:
        """创建卡片实体并发送

        使用 template 方式创建的卡片默认已开启流式更新模式。

        :param receive_id: 目标 ID
        :param template_id: 卡片模板 ID
        :param template_version_name: 模板版本号，如 "1.0.5"
        :param template_variable: 模板变量字典，如 {"content": "文本内容"}
        :param receive_id_type: 目标 ID 类型
        :return: 发送消息的响应数据（字典格式）
        """
        self._create_card_entity_with_streaming(
            template_id=template_id,
            template_version_name=template_version_name,
            template_variable=template_variable,
        )
        return self._send_card(receive_id=receive_id, receive_id_type=receive_id_type)

    def disable_streaming_mode(
        self,
        uuid_str: str | None = None,
    ) -> dict[str, Any]:
        """关闭流式更新模式

        :param uuid_str: 幂等 ID，如果不提供则自动生成
        :return: 响应数据（字典格式）
        """
        if not self.card_id:
            raise ValueError("卡片实体 ID 不存在")

        settings = {
            "config": {
                "streaming_mode": False,
            }
        }

        sequence = self._next_sequence()
        uuid_value = uuid_str or str(uuid.uuid4())

        return retry_feishu_api(
            api=update_card_entity_settings,
            args=[
                self.tenant_access_token,
                self.card_id,
                settings,
                sequence,
                uuid_value,
            ],
        )

    def update_text(
        self,
        element_id: str,
        content: str,
        uuid_str: str | None = None,
    ) -> dict[str, Any]:
        """流式更新文本

        :param element_id: 文本元素或富文本组件的 ID
        :param content: 新的全量文本内容
        :param uuid_str: 幂等 ID，如果不提供则自动生成
        :return: 响应数据（字典格式）
        """
        if not self.card_id:
            raise ValueError("卡片实体 ID 不存在")

        sequence = self._next_sequence()
        uuid_value = uuid_str or str(uuid.uuid4())

        return retry_feishu_api(
            api=update_card_element_content,
            args=[
                self.tenant_access_token,
                self.card_id,
                element_id,
                content,
                sequence,
                uuid_value,
            ],
        )
