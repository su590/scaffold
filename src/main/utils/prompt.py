"""
@Date    : 2026/5/15 16:25
@Author  : Chiang
@Desc    : None
"""
import threading

from src.main.constance import ROOT_PATH
from src.main.redis.cache import get_cache, set_cache
from src.main.utils.locktools import TmpIdLock

_KEY_PREFIX = 'prompts'
_lock = threading.Lock()

_prompts_dir_path = ROOT_PATH / 'src' / 'resources' / 'prompts'


def _get_prompt(prompt_name: str) -> str:
    concrete_prompt = _prompts_dir_path / prompt_name
    return concrete_prompt.read_text(encoding='utf-8')


def _get_prompt_key(key: str) -> str:
    return f'{_KEY_PREFIX}:{key}'


def _get_key_name(name: str) -> str:
    return name.replace('_', '-')


def _load_prompt(name: str) -> str:
    """
    获取prompt
    :param name:
    :return:
    """
    key_name = _get_key_name(name)
    prompt_key = _get_prompt_key(key_name)
    prompt = get_cache(prompt_key)
    if prompt:
        return prompt
    with TmpIdLock(f'prompts_tools:load_prompt:{name}'):
        prompt = get_cache(prompt_key)
        if prompt:
            return prompt
        prompt = _get_prompt(f'{name}.md')
        set_cache(prompt_key, prompt)
        return prompt
