"""
数据库模型基类

提供所有模型的基础类。
"""
from sqlalchemy.ext.declarative import declarative_base

# 创建基类
Base = declarative_base()
