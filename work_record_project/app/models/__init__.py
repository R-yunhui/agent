"""
数据模型

包含 Pydantic 模型（API 请求/响应）和 SQLModel 模型（数据库表）
"""

from work_record_project.app.models.chat_request import ChatRequest
from work_record_project.app.models.work_record import WorkRecordCreate, WorkRecordResponse
from work_record_project.app.models.database import WorkRecord, DailyReport, WeeklyReport

__all__ = [
    # Pydantic 模型
    "ChatRequest", 
    "WorkRecordCreate", 
    "WorkRecordResponse",
    # SQLModel 数据库模型
    "WorkRecord",
    "DailyReport", 
    "WeeklyReport",
]
