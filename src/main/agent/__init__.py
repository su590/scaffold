"""
@Date    : 2026/5/15 14:50
@Author  : Chiang
@Desc    : None
"""
import os

from src.main.config import get_config

os.environ["OPENAI_API_KEY"] = get_config("api_key")
