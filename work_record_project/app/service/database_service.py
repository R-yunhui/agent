"""
数据库服务层

使用 SQLModel + SQLite 替代 InMemoryStorage
"""
import os
import logging
from datetime import date, datetime
from typing import List, Optional
from functools import lru_cache

from sqlmodel import SQLModel, Session, create_engine, select

from work_record_project.app.models.database import WorkRecord, DailyReport, WeeklyReport

logger = logging.getLogger(__name__)

# 数据库文件路径（存放在 data 目录下）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'work_records.db')}"


@lru_cache()
def get_engine():
    """获取数据库引擎（单例）"""
    # 确保 data 目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
    logger.info(f"初始化数据库引擎: {DATABASE_URL}")
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # 设为 True 可查看 SQL 语句
        connect_args={"check_same_thread": False}  # SQLite 需要
    )
    
    # 创建表
    SQLModel.metadata.create_all(engine)
    logger.info("数据库表创建/检查完成")
    
    return engine


def get_session() -> Session:
    """获取数据库会话"""
    return Session(get_engine())


class DatabaseStorage:
    """
    数据库存储服务
    
    保持与 InMemoryStorage 相同的接口，方便替换
    """

    def save_work_record(self, record_date: date, data: dict) -> WorkRecord:
        """保存工作记录（存在则更新）"""
        with get_session() as session:
            # 查找是否存在
            statement = select(WorkRecord).where(WorkRecord.record_date == record_date)
            existing = session.exec(statement).first()
            
            if existing:
                # 更新
                existing.product = data.get("product", "")
                existing.project = data.get("project", "")
                existing.others = data.get("others", "")
                existing.risks = data.get("risks", "")
                existing.tomorrow = data.get("tomorrow", "")
                existing.updated_at = datetime.now()
                session.add(existing)
                session.commit()
                session.refresh(existing)
                logger.info(f"更新工作记录: date={record_date}")
                return existing
            else:
                # 新增
                record = WorkRecord(
                    record_date=record_date,
                    product=data.get("product", ""),
                    project=data.get("project", ""),
                    others=data.get("others", ""),
                    risks=data.get("risks", ""),
                    tomorrow=data.get("tomorrow", "")
                )
                session.add(record)
                session.commit()
                session.refresh(record)
                logger.info(f"新增工作记录: date={record_date}")
                return record

    def get_work_record(self, record_date: date) -> Optional[dict]:
        """获取单个工作记录"""
        with get_session() as session:
            statement = select(WorkRecord).where(WorkRecord.record_date == record_date)
            record = session.exec(statement).first()
            
            if record:
                return {
                    "record_date": record.record_date,
                    "product": record.product,
                    "project": record.project,
                    "others": record.others,
                    "risks": record.risks,
                    "tomorrow": record.tomorrow,
                    "created_at": record.created_at.isoformat()
                }
            return None

    def get_work_records_by_date_range(self, start_date: date, end_date: date) -> List[dict]:
        """获取指定日期范围内的工作记录"""
        with get_session() as session:
            statement = (
                select(WorkRecord)
                .where(WorkRecord.record_date >= start_date)
                .where(WorkRecord.record_date <= end_date)
                .order_by(WorkRecord.record_date)
            )
            records = session.exec(statement).all()
            
            return [
                {
                    "record_date": r.record_date,
                    "product": r.product,
                    "project": r.project,
                    "others": r.others,
                    "risks": r.risks,
                    "tomorrow": r.tomorrow,
                    "created_at": r.created_at.isoformat()
                }
                for r in records
            ]

    def save_daily_report(self, report_date: date, report_content: str) -> DailyReport:
        """保存日报（存在则更新）"""
        with get_session() as session:
            statement = select(DailyReport).where(DailyReport.report_date == report_date)
            existing = session.exec(statement).first()
            
            if existing:
                existing.content = report_content
                existing.updated_at = datetime.now()
                session.add(existing)
                session.commit()
                session.refresh(existing)
                logger.info(f"更新日报: date={report_date}")
                return existing
            else:
                report = DailyReport(
                    report_date=report_date,
                    content=report_content
                )
                session.add(report)
                session.commit()
                session.refresh(report)
                logger.info(f"新增日报: date={report_date}")
                return report

    def get_daily_report(self, report_date: date) -> Optional[str]:
        """获取日报"""
        with get_session() as session:
            statement = select(DailyReport).where(DailyReport.report_date == report_date)
            report = session.exec(statement).first()
            return report.content if report else None

    def save_weekly_report(
        self, 
        report_start_date: date, 
        report_end_date: date, 
        report_content: str
    ) -> WeeklyReport:
        """保存周报（存在则更新）"""
        with get_session() as session:
            statement = (
                select(WeeklyReport)
                .where(WeeklyReport.start_date == report_start_date)
                .where(WeeklyReport.end_date == report_end_date)
            )
            existing = session.exec(statement).first()
            
            if existing:
                existing.content = report_content
                existing.updated_at = datetime.now()
                session.add(existing)
                session.commit()
                session.refresh(existing)
                logger.info(f"更新周报: {report_start_date} ~ {report_end_date}")
                return existing
            else:
                report = WeeklyReport(
                    start_date=report_start_date,
                    end_date=report_end_date,
                    content=report_content
                )
                session.add(report)
                session.commit()
                session.refresh(report)
                logger.info(f"新增周报: {report_start_date} ~ {report_end_date}")
                return report

    def get_weekly_report(self, report_start_date: date, report_end_date: date) -> Optional[str]:
        """获取周报"""
        with get_session() as session:
            statement = (
                select(WeeklyReport)
                .where(WeeklyReport.start_date == report_start_date)
                .where(WeeklyReport.end_date == report_end_date)
            )
            report = session.exec(statement).first()
            return report.content if report else None


# 全局单例（保持与 InMemoryStorage 相同的使用方式）
storage = DatabaseStorage()

