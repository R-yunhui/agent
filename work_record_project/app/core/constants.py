"""
常量定义
"""
from enum import Enum


class ReportType(str, Enum):
    """
    报告类型枚举
    定义了两种报告类型：日常报告和周报报告。
    """

    DAILY = "daily"
    WEEKLY = "weekly"

    def __str__(self) -> str:
        """返回枚举值的字符串表示"""
        return self.value

    @property
    def description(self) -> str:
        """返回模式的中文描述"""
        descriptions = {
            ReportType.DAILY: "日报",
            ReportType.WEEKLY: "周报",
        }
        return descriptions.get(self, "未知")
