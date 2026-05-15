"""
@Date    : 2026/5/15 16:21
@Author  : Chiang
@Desc    : None
"""

import datetime

from flask import Blueprint

bp = Blueprint("hello", __name__)


@bp.route("", methods=["GET"])
def _() -> str:
    """
    hello
    :return:
    """
    return f"Hello At {datetime.datetime.now()}!"
