"""
@Author   : hcq
@Time     : 2026/1/5 16:30
@Desc     : 统筹数据库相关组件及其方法

"""

import logging

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.main.config import get_config

config: dict = get_config("mysql")


def _get_mysql_url() -> str:
    """从配置文件读取 MySQL 连接 URL"""
    return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"


def _create_engine() -> Engine:
    logging.info(f"database >> host: {config['host']}")
    logging.info(f"database >> port: {config['port']}")
    logging.info(f"database >> database: {config['database']}")
    logging.info(f"database >> user: {config['user']}")
    return create_engine(
        _get_mysql_url(),
        echo=config["engine"]["echo"],
        pool_size=config["engine"]["pool_size"],  # 增加连接池大小
        max_overflow=config["engine"]["max_overflow"],  # 增加溢出数量
        pool_timeout=config["engine"]["pool_timeout"],  # 设置超时时间
        pool_recycle=config["engine"]["pool_recycle"],
        pool_pre_ping=config["engine"]["pool_pre_ping"],
    )


engine = _create_engine()
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
base = declarative_base()
