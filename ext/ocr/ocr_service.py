"""
@Date    : 2026/5/20 18:36
@Author  : Chiang
@Desc    : None
"""
import base64
import io
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

import requests
from PIL import Image
from ext.ocr.ocr_error import DownLoadError, ReadFileError, ImageToBase64Error, OcrApiCallError

logger = logging.getLogger(__name__)

# OCR API配置
OCR_URL = "http://183.36.251.69:1234/ocr"


class OCRService:
    """OCR服务类，提供图片OCR识别功能"""

    def __init__(self, ocr_url: str | None = None):
        """
        初始化OCR服务
        """
        if ocr_url:
            self._ocr_url = ocr_url
        else:
            self._ocr_url = OCR_URL

    @staticmethod
    def _is_url(path: str) -> bool:
        """
        判断是否为URL链接

        :param path: 路径或URL
        :return: 如果是URL返回True，否则返回False
        """
        return path.startswith(('http://', 'https://'))

    @staticmethod
    def _is_base64_data_url(path: str) -> bool:
        return path.startswith("data:image/") and ";base64," in path

    @staticmethod
    def _read_base64_data_url(data_url: str) -> bytes:
        try:
            _, base64_data = data_url.split(",", 1)
            if not base64_data:
                return b""
            return base64.b64decode(base64_data)
        except Exception as e:
            raise ReadFileError(f"读取base64图片失败: {str(e)}") from e

    @staticmethod
    def _download_image(url: str) -> bytes:
        """
        从URL下载图片

        :param url: 图片URL
        :return: 图片的二进制数据
        """
        try:
            logger.info(f"正在下载图片: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise DownLoadError(f"下载图片失败: {str(e)}") from e

    @staticmethod
    def _read_local_file(file_path: str) -> bytes:
        """
        读取本地文件

        :param file_path: 本地文件路径
        :return: 文件的二进制数据
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            logger.info(f"正在读取本地文件: {file_path}")
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise ReadFileError(f"读取文件失败: {str(e)}") from e

    @staticmethod
    def _compress_image(image: Image.Image, image_format: str = "JPEG", quality: int = 60) -> io.BytesIO:
        """
        压缩图片

        :param image: PIL Image对象
        :param image_format: 图片格式
        :param quality: 压缩质量（1-100）
        :return: 压缩后的图片数据流
        """
        buffer = io.BytesIO()
        image.save(buffer, format=image_format, quality=quality)
        buffer.seek(0)
        return buffer

    def _image_to_base64(self, image_data: bytes) -> str:
        """
        将图片数据转换为base64编码

        :param image_data: 图片的二进制数据
        :return: base64编码的图片数据
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            image_format = image.format or "JPEG"
            logger.info(f"图片类型为: {image_format}")

            compressed_image = self._compress_image(image, image_format=image_format)
            image_base64 = base64.b64encode(compressed_image.getvalue()).decode('utf-8')

            return image_base64
        except Exception as e:
            raise ImageToBase64Error(f"图片转换为base64失败: {str(e)}") from e

    def _process_image_path(self, image_path: str) -> bytes:
        """
        处理图片路径，返回图片数据

        :param image_path: 图片路径或URL
        :return: 图片的二进制数据
        """
        if self._is_base64_data_url(image_path):
            image_data = self._read_base64_data_url(image_path)
        elif self._is_url(image_path):
            # URL链接，下载图片
            image_data = self._download_image(image_path)
        else:
            # 本地路径，读取文件
            image_data = self._read_local_file(image_path)

        return image_data

    def _call_ocr_api(self, base64_data: str) -> Dict[str, Any]:
        """
        调用OCR API

        :param base64_data: base64编码的图片数据
        :return: OCR API返回的结果
        """
        try:
            logger.info("正在调用OCR API...")
            response = requests.post(self._ocr_url, json={"img": base64_data}, timeout=60)
            response.raise_for_status()
            result = response.json()
            logger.info("OCR API调用成功")
            return result
        except Exception as e:
            raise OcrApiCallError(f"OCR API调用失败: {str(e)}") from e

    def _recognize_single_image(self, image_path: str) -> Dict[str, Any]:
        """
        处理单张图片的OCR识别

        :param image_path: 图片路径或URL
        :return: 单张图片的OCR识别结果，格式为:
            {
                "image_path": "图片路径",
                "text": "该图片识别的文本",
                "raw_result": {}  # OCR API原始返回结果
            }
        """
        logger.info(f"处理图片: {image_path}")

        # 处理图片路径，获取图片数据
        image_data = self._process_image_path(image_path)
        if not image_data:
            return {
                "image_path": image_path,
                "text": "",
                "raw_result": {}
            }

        # 转换为base64
        base64_data = self._image_to_base64(image_data)

        # 调用OCR API
        ocr_result = self._call_ocr_api(base64_data)

        # 提取文本
        image_text = ""
        if 'data' in ocr_result:
            for item in ocr_result['data']:
                if 'text' in item:
                    image_text += item['text'] + "\n"

        return {
            "image_path": image_path,
            "text": image_text.strip(),
            "raw_result": ocr_result
        }

    def recognize(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        对图片列表进行OCR识别（使用线程池并行处理）

        :param image_paths: 图片路径或URL列表
        :return: OCR识别结果列表，每个元素格式为:
            {
                "image_path": "图片路径",
                "text": "该图片识别的文本",
                "raw_result": {}  # OCR API原始返回结果
            }
        :raises: 如果处理失败，直接抛出相应的异常
        """
        if not image_paths:
            raise ValueError("图片路径列表为空")

        results = []

        # 使用线程池并行处理多张图片
        with ThreadPoolExecutor(max_workers=min(len(image_paths), 10)) as executor:
            # 提交所有任务
            future_to_path = {
                executor.submit(self._recognize_single_image, image_path): image_path
                for image_path in image_paths
            }

            # 收集结果，保持顺序
            path_to_result = {}
            for future in as_completed(future_to_path):
                image_path = future_to_path[future]
                result = future.result()
                path_to_result[image_path] = result

        # 按照原始顺序返回结果
        for image_path in image_paths:
            results.append(path_to_result[image_path])

        logger.info("所有图片OCR识别完成")
        return results


ocr_service = OCRService()
