"""
API 路由
"""

from fastapi import APIRouter, HTTPException
from datetime import date, datetime
import logging
from app.service import storage
from app.models import WorkRecordCreate, WorkRecordResponse
from app.service import create_daily_report as generate_report_content

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/records", tags=["工作记录"])

@router.post("/", response_model=WorkRecordResponse)
async def create_work_record(work_record: WorkRecordCreate):
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
    
    
@router.post("/daily/generate", response_model=str)
async def generate_daily_report(record_date: date = None):
    """
    生成日报
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
        return report_content
    except Exception as e:
        logger.error(f"AI 生成日报失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成日报失败: {str(e)}")