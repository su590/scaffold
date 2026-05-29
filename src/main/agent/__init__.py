"""
@Date    : 2026/5/15 14:50
@Author  : Chiang
@Desc    : None
"""
import os

from src.main.config import get_config

# 配置相应的key
os.environ["OPENAI_API_KEY"] = get_config("api_key")

# langsmith流程监控
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"] = get_config("langsmith_api_key")
os.environ["LANGSMITH_PROJECT"] = "put-your-project-name-here"
