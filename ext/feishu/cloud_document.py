"""
@Author   : hcq
@Desc     : 飞书云文档

"""

import enum
import logging
import traceback
from abc import ABC, abstractmethod
from typing import Optional

import requests
from pydantic import BaseModel, Field

from ext.feishu.header import compose_headers
from ext.feishu.retry import retry_feishu_api


def download_media(
    tenant_access_token: str,
    file_token: str,
    extra: Optional[str] = None,
    range_header: Optional[str] = None,
) -> requests.Response:
    """下载云文档中的素材（图片、文件等） 该接口调用频率上限为 5 QPS，10000 次/天

    参考 https://open.feishu.cn/document/server-docs/docs/drive-v1/media/download

    :param tenant_access_token: 应用token
    :param file_token: 素材文件的token（从文档块中获取的File Block或Image Block的token）
    :param extra: 拥有高级权限的多维表格在下载素材时，需要添加额外的扩展信息作为URL查询参数鉴权
    :param range_header: 分片下载范围，格式为 "bytes=start-end"，例如 "bytes=0-1024"
    :return: 响应对象，可通过response.content获取二进制数据
    :raises: requests.RequestException
    """
    url = f"https://open.feishu.cn/open-apis/drive/v1/medias/{file_token}/download"

    headers = compose_headers(tenant_access_token)
    if range_header:
        headers["Range"] = range_header

    params = {}
    if extra:
        params["extra"] = extra

    return requests.get(
        url=url,
        headers=headers,
        params=params if params else None,
    )


def _get_document_blocks(
    tenant_access_token: str,
    document_id: str,
    page_token: Optional[str],
    page_size: int,
) -> requests.Response:
    """获取云文档内容

    获取文档当中所有的块 https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/list
    块的数据结构 https://open.feishu.cn/document/docs/docs/data-structure/block#e8ce4e8e
    无需在云文档当中添加相应的应用 应该是在获取了统一的权限之后 该应用就有了所有云文档的阅读权限
    :param tenant_access_token: 应用token
    :param document_id: 文档ID
    :param page_token: 分页标记，首次调用不传，使用响应中的page_token继续请求
    :param page_size: 分页大小
    :return: 响应
    """
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks"
    params: dict = {"page_size": page_size}
    if page_token:
        params["page_token"] = page_token

    return requests.get(
        url=url,
        headers=compose_headers(tenant_access_token),
        params=params,
    )


class ResponseShortCut(BaseModel):
    has_more: bool
    page_token: Optional[str] = ""
    items: list[dict]


def _get_all_document_blocks(
    tenant_access_token: str,
    document_id: str,
    page_token: Optional[str] = None,
    page_size: int = 500,
) -> list[dict]:
    # 在CloudDocumentResolver的实现类里面去判断图片的数量来判断文档是否过大
    res: list[dict] = []
    response_json = retry_feishu_api(
        _get_document_blocks,
        args=[tenant_access_token, document_id, page_token, page_size],
    )
    rsc = ResponseShortCut(**response_json["data"])
    res.extend(rsc.items)
    while rsc.has_more:
        response_json = retry_feishu_api(
            _get_document_blocks,
            args=[tenant_access_token, document_id, rsc.page_token, page_size],
        )
        rsc = ResponseShortCut(**response_json["data"])
        res.extend(rsc.items)
    return res


class BlockType(enum.Enum):
    Page = 1  # 页面
    Text = 2  # 文本
    Heading1 = 3  # 标题1
    Heading2 = 4  # 标题2
    Heading3 = 5  # 标题3
    Bullet = 12  # 无序列表
    Ordered = 13  # 有序列表
    File = 23  # 文件
    Image = 27  # 图片


class BaseBlock(BaseModel):
    block_id: str
    block_type: int
    parent_id: str = ""


def extract_text_from_elements(data: dict) -> str:
    """从dict中提取elements并解析文本内容"""
    elements = data["elements"]
    texts = []
    for element in elements:
        # 文本元素
        try:
            texts.append(element["text_run"]["content"])
        except KeyError:
            # element当中有的为属性 直接跳过即可
            continue
    return "".join(texts)


class Page(BaseBlock):
    children: list[str] = Field(default_factory=list)
    page: dict = Field(default_factory=dict)

    def get_markdown(self) -> str:
        """解析页面内容"""
        return extract_text_from_elements(self.page)


class Text(BaseBlock):
    text: dict = Field(default_factory=dict)

    def get_markdown(self) -> str:
        """解析文本内容"""
        return extract_text_from_elements(self.text)


class Heading1(BaseBlock):
    heading1: dict = Field(default_factory=dict)

    def get_markdown(self) -> str:
        """解析标题1内容，Markdown格式"""
        text = extract_text_from_elements(self.heading1)
        return f"# {text}" if text else ""


class Heading2(BaseBlock):
    heading2: dict = Field(default_factory=dict)

    def get_markdown(self) -> str:
        """解析标题2内容，Markdown格式"""
        text = extract_text_from_elements(self.heading2)
        return f"## {text}" if text else ""


class Heading3(BaseBlock):
    heading3: dict = Field(default_factory=dict)

    def get_markdown(self) -> str:
        """解析标题3内容，Markdown格式"""
        text = extract_text_from_elements(self.heading3)
        return f"### {text}" if text else ""


class Bullet(BaseBlock):
    bullet: dict = Field(default_factory=dict)

    def get_markdown(self) -> str:
        """解析无序列表内容，Markdown格式"""
        text = extract_text_from_elements(self.bullet)
        return f"- {text}" if text else ""


class Ordered(BaseBlock):
    ordered: dict = Field(default_factory=dict)

    def get_markdown(self) -> str:
        """解析有序列表内容，Markdown格式"""
        text = extract_text_from_elements(self.ordered)
        return text


class _MergeInfo(BaseModel):
    """表格单元格合并信息"""

    col_span: int = 1  # 列跨度，合并了多少列
    row_span: int = 1  # 行跨度，合并了多少行


class _TablePropertyProperty(BaseModel):
    """表格属性配置"""

    column_size: int = 0  # 表格列数
    column_width: list[int] = Field(default_factory=list)  # 每列的宽度（像素）
    merge_info: list[_MergeInfo] = Field(default_factory=list)  # 每个单元格的合并信息
    row_size: int = 0  # 表格行数


class TableProperty(BaseModel):
    cells: list[str] = Field(default_factory=list)
    property: _TablePropertyProperty = Field(default_factory=_TablePropertyProperty)


class Table(BaseBlock):
    # 表格的处理太麻烦 但其中的内容会以其他的block形式给出来 相当于Table只是一个载体 所以在这里就直接不处理了
    table: TableProperty = Field(default_factory=TableProperty)


class File(BaseBlock):
    file: dict = Field(default_factory=dict)

    def get_token(self) -> str:
        """获取文件token"""
        return self.file["token"]


class Image(BaseBlock):
    image: dict = Field(default_factory=dict)

    def get_token(self) -> str:
        """获取图片token"""
        return self.image["token"]


enum_class_map = {
    BlockType.Page: Page,
    BlockType.Text: Text,
    BlockType.Heading1: Heading1,
    BlockType.Heading2: Heading2,
    BlockType.Heading3: Heading3,
    BlockType.Bullet: Bullet,
    BlockType.Ordered: Ordered,
    BlockType.File: File,
    BlockType.Image: Image,
}


def _dict2block(dicts: list[dict]) -> list[BaseBlock]:
    """将字典列表转换为Block对象生成器"""
    res: list[BaseBlock] = []
    for data in dicts:
        try:
            block_type_value = data["block_type"]

            try:
                block_type = BlockType(block_type_value)
            except ValueError:
                # block_type不在枚举中
                logging.warning(f"未知block_type: {block_type_value}")
                continue

            res.append(enum_class_map[block_type](**data))
        except Exception as e:
            # 其他异常（如缺少必需字段），尝试使用基础Block
            logging.error(f"解析block异常: {e}\n{traceback.format_exc()}")
            continue
    return res


class CloudDocumentResolver(ABC):
    """
    飞书云文档内容解析
    """

    def __init__(self, token: str, document_id: str):
        self._token = token
        self._document_id = document_id

    def get_markdown_content(
        self,
    ) -> str:
        # 获取到云文档当中所有的blocks
        dct = _get_all_document_blocks(self._token, self._document_id)
        blocks: list[BaseBlock] = _dict2block(dct)

        contents: list[str] = []
        image_tokens: list[str] = []
        image_indices: list[int] = []  # 记录图片在contents中的位置索引

        # 计算有序列表的顺序
        order_sequence = 1

        # 遍历所有block
        for block in blocks:
            if isinstance(block, File):
                file_token = block.get_token()
                file_content = self.file_resolver(file_token)
                contents.append(file_content)
            elif isinstance(block, Image):
                image_token = block.get_token()
                image_tokens.append(image_token)
                image_indices.append(len(contents))
                contents.append("")  # 占位符，后续会被替换
            elif isinstance(block, Ordered):
                sequence = block.ordered["style"]["sequence"]
                if sequence == "1":
                    order_sequence = 1
                contents.append(f"{order_sequence}. {block.get_markdown()}")
                order_sequence += 1
            else:
                contents.append(block.get_markdown())

        # 批量解析所有图片
        if image_tokens:
            image_contents = self.image_resolver(image_tokens)
            # 按照顺序将图片内容插入到对应位置
            for idx, image_content in zip(image_indices, image_contents):
                contents[idx] = image_content

        return "\n".join(contents)

    @abstractmethod
    def file_resolver(self, file_token: str) -> str:
        """解析文件，返回文件内容或路径"""
        pass

    @abstractmethod
    def image_resolver(self, image_tokens: list[str]) -> list[str]:
        """解析图片，返回图片URL或路径"""
        pass
