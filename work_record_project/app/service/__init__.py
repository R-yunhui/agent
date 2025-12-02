# 使用数据库存储（替代 InMemoryStorage）
from work_record_project.app.service.database_service import storage
from work_record_project.app.service.chat_service import chat_with_llm, chat_with_llm_sync, clear_session_history
from work_record_project.app.service.llm_report_service import create_daily_report, create_weekly_report
from work_record_project.app.service.llm_rag import embedding_with_llm, search_similar_documents

__all__ = [
    "storage",
    "create_daily_report",
    "create_weekly_report",
    "chat_with_llm",
    "chat_with_llm_sync",
    "clear_session_history",
    "embedding_with_llm",
    "search_similar_documents",
]
