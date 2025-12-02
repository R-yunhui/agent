"""
SQLModel 数据库模型定义

使用 SQLite 存储工作记录、日报、周报
"""
from datetime import date, datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class WorkRecord(SQLModel, table=True):
    """工作记录表"""
    __tablename__ = "work_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    record_date: date = Field(index=True, unique=True, description="记录日期")
    product: str = Field(default="", description="产品相关工作记录")
    project: str = Field(description="项目相关工作记录")
    others: str = Field(default="", description="其他工作记录")
    risks: str = Field(default="", description="风险和问题")
    tomorrow: str = Field(description="明天计划")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class DailyReport(SQLModel, table=True):
    """日报表"""
    __tablename__ = "daily_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_date: date = Field(index=True, unique=True, description="日报日期")
    content: str = Field(description="日报内容 (Markdown)")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class WeeklyReport(SQLModel, table=True):
    """周报表"""
    __tablename__ = "weekly_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    start_date: date = Field(index=True, description="开始日期")
    end_date: date = Field(index=True, description="结束日期")
    content: str = Field(description="周报内容 (Markdown)")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

