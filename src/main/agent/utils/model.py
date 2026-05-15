"""
@Date    : 2026/5/15 14:49
@Author  : Chiang
@Desc    : None
"""
from enum import Enum

from langchain_openai import ChatOpenAI

BASE_URL = "https://ark.cn-beijing.volces.com/api/v3/"


class DoubaoModel(Enum):
    doubao_seed_1_8 = "doubao-seed-1-8-251228"
    doubao_seed_2_0_pro = "doubao-seed-2-0-pro-260215"


class ReasoningEffort(Enum):
    minimal = "minimal"
    low = "low"
    medium = "medium"
    high = "high"


def get_model(
        *,
        model: DoubaoModel = DoubaoModel.doubao_seed_1_8,
        timeout: int = 60,
        **kwargs,
) -> ChatOpenAI:
    return ChatOpenAI(
        base_url=BASE_URL,
        model=model.value,
        timeout=timeout,
        temperature=0.2,
        max_retries=3,
        streaming=False,
        reasoning_effort=ReasoningEffort.minimal.value,
        model_kwargs={"parallel_tool_calls": False},
        **kwargs,
    )


model = get_model(model=DoubaoModel.doubao_seed_1_8, timeout=300)
