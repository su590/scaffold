"""
@Date    : 2026/5/15 16:22
@Author  : Chiang
@Desc    : None
"""
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


def _register_jobs():
    """注册定时任务"""
    pass


def start_scheduler():
    """启动定时器"""
    _register_jobs()
    scheduler.start()
