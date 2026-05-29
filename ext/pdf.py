"""
@Date: 2026/5/29
@Author: Chiang
@Desc: pdf转图片
"""
import base64
import io
from typing import List

import fitz  # PyMuPDF
import requests
from PIL import Image


def pdf_url_to_images(
        pdf_url: str,
        output_format: str = "jpeg",
        scale: float = 1.5,
        jpeg_quality: int = 75,
        return_base64: bool = True
) -> List[str]:
    """
    下载 PDF 并转为图片列表（Base64 或 bytes）

    :param pdf_url: PDF 网络地址
    :param output_format: 输出格式 "png" 或 "jpeg"
    :param scale: 页面渲染放大倍数
    :param jpeg_quality: JPEG 压缩质量，仅对 jpeg 有效
    :param return_base64: 是否返回 Base64 字符串
    :return: 图片列表（Base64 或 bytes）
    """
    response = requests.get(pdf_url)
    response.raise_for_status()

    pdf_document = fitz.open(stream=response.content, filetype="pdf")
    images: List[str] = []

    try:
        for page in pdf_document:
            # 渲染页面
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # 转 PIL Image 方便压缩和格式转换
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            buf = io.BytesIO()
            if output_format.lower() == "jpeg":
                img.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
            else:
                img.save(buf, format="PNG", optimize=True)

            buf.seek(0)
            img_bytes = buf.read()

            if return_base64:
                b64_str = base64.b64encode(img_bytes).decode("utf-8")
                images.append(f"data:image/{output_format.lower()};base64,{b64_str}")
            else:
                images.append(img_bytes)

        if not images:
            raise ValueError("PDF 没有可转换的页面")
        return images
    finally:
        pdf_document.close()
