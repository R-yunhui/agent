"""
API 路由聚合器

这里统一管理所有的 API 路由，方便在 main.py 中一次性注册。
"""

from fastapi import APIRouter
from work_record_project.app.api import records, chat

# 后续可以添加其他路由
# from app.api import daily, weekly

# 创建总路由
api_router = APIRouter()

# 注册各个子路由
api_router.include_router(records.router)

api_router.include_router(chat.router)
