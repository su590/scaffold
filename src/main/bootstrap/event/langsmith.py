"""
@Date    : 2026/5/15 14:41
@Author  : Chiang
@Desc    : None
"""
import os

from src.main.config import get_config


def init_langsmith() -> None:
    # 测试环境设置相应的langsmith进行流程的监控
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGSMITH_API_KEY"] = get_config("langsmith_api_key")
    os.environ["LANGSMITH_PROJECT"] = "recruitment-ai-agent"
