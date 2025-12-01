from typing import Optional

from pydantic import BaseModel
from pydantic.fields import Field


class DailyWorkReport(BaseModel):
    """
    每日工作报告模型
    """
    date: Optional[str] = Field(..., description="日期，格式为YYYY-MM-DD")
    content: Optional[str] = Field(..., description="工作内容")


class WeeklyWorkReport(BaseModel):
    """
    每周工作报告模型
    """
    start_date: Optional[str] = Field(..., description="开始日期，格式为YYYY-MM-DD")
    end_date: Optional[str] = Field(..., description="结束日期，格式为YYYY-MM-DD")
    content: Optional[str] = Field(..., description="工作内容")
