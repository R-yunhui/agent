from pydantic.fields import Field
from typing import Optional
from pydantic import BaseModel
from datetime import date

class WorkRecordCreate(BaseModel):
    """
    创建工作记录的对象
    """
    
    record_date: Optional[date] = Field(None, description="记录日期,默认为当前日期")
    product: Optional[str] = Field("", description="产品相关工作记录")
    project: str = Field(..., min_length=1, description="项目相关工作记录（必填）")
    others: Optional[str] = Field("", description="其他工作记录")
    risks: Optional[str] = Field("", description="风险和问题")
    tomorrow: str = Field(..., description="明天计划做什么")
    
    class Config:
        json_schema_extra = {
            "example": {
                "record_date": "2025-11-30",
                "product": "完成用户画像功能需求评审",
                "project": "完成XX项目登录模块开发，对接支付接口",
                "others": "参加技术分享会",
                "risks": "数据库性能存在瓶颈",
                "tomorrow": "优化数据库查询，完成订单模块"
            }
        }
        
class WorkRecordResponse(BaseModel):
    """工作记录响应"""
    
    record_date: date
    product: str
    project: str
    others: str
    risks: str
    tomorrow: str
    created_at: str  # 记录创建时间