"""
Pydantic 数据模型
"""

from work_record_project.app.models.chat_request import ChatRequest
from work_record_project.app.models.work_record import WorkRecordCreate
from work_record_project.app.models.work_record import WorkRecordResponse

__all__ = ["ChatRequest", "WorkRecordCreate", "WorkRecordResponse"]
