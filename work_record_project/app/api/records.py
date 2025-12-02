"""
API 路由
"""
from typing import List

from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import date, datetime
import logging
from work_record_project.app.service import storage
from work_record_project.app.models import WorkRecordCreate, WorkRecordResponse
from work_record_project.app.core import ReportType
from work_record_project.app.service import create_daily_report as generate_report_content, \
    create_weekly_report as generate_weekly_report_content, \
    embedding_with_llm as embed_report_content

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/records", tags=["工作记录"])


@router.post("/", response_model=WorkRecordResponse)
def create_work_record(work_record: WorkRecordCreate):
    """
    添加工作记录
    """
    # 如果没有提供日期，使用今天
    record_date = work_record.record_date or date.today()
    logger.info(f"收到添加工作记录请求: date={record_date}")

    # 保存到存储
    record_data = work_record.model_dump()
    record_data['record_date'] = record_date
    storage.save_work_record(record_date, record_data)
    logger.info(f"工作记录保存成功: date={record_date}")

    # 返回结果（添加 created_at 字段）
    return WorkRecordResponse(
        record_date=record_date,
        product=work_record.product or "",
        project=work_record.project,
        others=work_record.others or "",
        risks=work_record.risks or "",
        tomorrow=work_record.tomorrow,
        created_at=datetime.now().isoformat()
    )


@router.get("/", response_model=List[WorkRecordResponse])
def get_work_records(start_date: date, end_date: date):
    """
    获取指定日期范围内的工作记录
    """
    logger.info(f"收到获取工作记录请求: start_date={start_date}, end_date={end_date}")

    # 验证日期顺序
    if start_date > end_date:
        logger.warning(f"无效日期范围: start_date={start_date} > end_date={end_date}")
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    # 从存储获取记录
    records = storage.get_work_records_by_date_range(start_date, end_date)
    logger.info(f"成功获取 {len(records)} 条工作记录")

    return records


@router.post("/daily/generate", response_model=str)
def generate_daily_report(
        record_date: date = None,
        background_tasks: BackgroundTasks = None
):
    """
    生成日报
    
    生成完成后会在后台异步执行向量化存储，用于后续语义检索。
    """
    # 默认为今天
    target_date = record_date or date.today()
    logger.info(f"收到生成日报请求: date={target_date}")

    # 1. 获取工作记录
    record_data = storage.get_work_record(target_date)
    if not record_data:
        logger.warning(f"未找到日期 {target_date} 的工作记录")
        raise HTTPException(status_code=404, detail=f"未找到日期 {target_date} 的工作记录")

    # 2. 转换为模型对象
    try:
        work_record = WorkRecordCreate(**record_data)
    except Exception as e:
        logger.error(f"数据格式转换错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据格式错误: {str(e)}")

    # 3. 调用 AI 生成日报
    try:
        logger.info(f"开始调用 AI 生成日报: date={target_date}")
        report_content = generate_report_content(work_record)
        logger.info(f"日报生成成功: date={target_date}")

        # 4. 存储日报信息
        storage.save_daily_report(target_date, report_content)

        # 5. 后台异步执行向量化存储（用于语义检索）
        if background_tasks:
            background_tasks.add_task(
                embed_report_content,
                target_date,
                target_date,
                report_content,
                ReportType.DAILY  # 日报类型
            )
            logger.info(f"已添加日报向量化任务到后台队列: date={target_date}")

        return report_content
    except Exception as e:
        logger.error(f"AI 生成日报失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成日报失败: {str(e)}")


@router.post("/weekly/generate", response_model=str)
def generate_weekly_report(
        start_date: date,
        end_date: date,
        background_tasks: BackgroundTasks = None
):
    """
    生成周报
    
    生成完成后会在后台异步执行向量化存储，用于后续语义检索。
    """
    if start_date is None or end_date is None:
        logger.warning("生成周报请求缺少日期范围")
        raise HTTPException(status_code=400, detail="生成周报请求缺少日期范围")

    if start_date > end_date:
        logger.warning(f"无效日期范围: start_date={start_date} > end_date={end_date}")
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    # 1. 获取指定日期范围内的工作记录
    records = storage.get_work_records_by_date_range(start_date, end_date)
    if not records:
        logger.warning(f"在日期范围 {start_date} 到 {end_date} 内未找到任何工作记录")
        raise HTTPException(status_code=404, detail=f"在日期范围 {start_date} 到 {end_date} 内未找到任何工作记录")

    # 2. 调用 AI 生成周报
    try:
        logger.info(f"开始调用 AI 生成周报: start_date={start_date}, end_date={end_date}")
        report_content = generate_weekly_report_content(start_date, end_date)
        logger.info(f"周报生成成功: start_date={start_date}, end_date={end_date}")

        # 3. 存储周报信息
        storage.save_weekly_report(start_date, end_date, report_content)

        # 4. 后台异步执行向量化存储（用于语义检索）
        if background_tasks:
            background_tasks.add_task(
                embed_report_content,
                start_date,
                end_date,
                report_content,
                ReportType.WEEKLY  # 周报类型
            )
            logger.info(f"已添加周报向量化任务到后台队列: {start_date} ~ {end_date}")

        return report_content
    except Exception as e:
        logger.error(f"AI 生成周报失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成周报失败: {str(e)}")
