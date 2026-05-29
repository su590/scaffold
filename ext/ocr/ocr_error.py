"""
@Date    : 2026/5/20 18:37
@Author  : Chiang
@Desc    : None
"""


class OcrBaseError(Exception):
    _msg = 'ocr错误'


class DownLoadError(OcrBaseError):
    _msg = '下载图片错误'


class ReadFileError(OcrBaseError):
    _msg = '读取文件错误'


class ImageToBase64Error(OcrBaseError):
    _msg = '图片转换为base64失败'


class OcrApiCallError(OcrBaseError):
    _msg = 'OCR API调用失败'
