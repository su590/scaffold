"""
@Date    : 2026/5/15 14:52
@Author  : Chiang
@Desc    : None
"""
import datetime

from langchain.agents.middleware import ToolRetryMiddleware

from src.main.bootstrap.event.log import logger


def on_tool_failure(exc: Exception) -> str:
    """
    工具调用失败后的处理：直接抛出 ToolCallError 兜底需要catch此异常

    Args:
        exc: 捕获的异常

    Returns:
        返回给LLM的错误信息
    """
    exc_type = type(exc).__name__
    exc_msg = str(exc)

    # 抛出异常
    alert_content = (
        f"AI工具调用失败告警\n\n"
        f"错误类型: {exc_type}\n"
        f"错误信息: {exc_msg}\n"
        f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    logger.error(alert_content)
    raise ValueError(alert_content)


tools_retry = ToolRetryMiddleware(
    max_retries=2,
    retry_on=(Exception,),
    on_failure=on_tool_failure,
    backoff_factor=2.0,
    initial_delay=1.0,
    max_delay=30.0,
    jitter=True,
)
