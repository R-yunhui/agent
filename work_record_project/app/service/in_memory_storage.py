# 暂通过内存存储的方式

from typing import Dict, List 
from datetime import date

class InMemoryStorage:
    def __init__(self):
        # 工作记录 key：日期字符串 value：工作记录
        self.work_records: Dict[str, dict] = {}
        
        # 日报 key：日期字符串 value：日报
        self.daily_reports: Dict[str, dict] = {}
        
        # 周报 key：日期字符串 value：周报
        self.weekly_reports: Dict[str, dict] = {}
        
    def save_work_record(self, record_date: date, data: dict):
        """
        保存工作记录
        """
        date_str = record_date.isoformat()
        self.work_records[date_str] = data
        
    def get_work_record(self, record_date: date) -> dict:
        """
        获取工作记录
        """
        date_str = record_date.isoformat()
        return self.work_records.get(date_str, {})
    
    def get_work_records_by_date_range(self, start_date: date, end_date: date) -> List[dict]:
        """
        获取指定日期范围内的工作记录
        """
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
        return [self.work_records.get(date_str, {}) for date_str in self.work_records if start_date_str <= date_str <= end_date_str]
        
        
# 全局单例
storage = InMemoryStorage()