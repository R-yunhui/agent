"""
大模型服务

大模型聊天相关逻辑，支持 RAG（检索增强生成）
"""

import os
import logging
from datetime import date, datetime
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnableWithMessageHistory
from langchain_core.documents import Document
from langchain_community.chat_message_histories import ChatMessageHistory

from work_record_project.app.service.llm_rag import search_similar_documents

# 加载 env
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 配置 ====================

# RAG 相关配置
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))  # 检索结果数量
RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.5"))  # 相似度阈值


# ==================== 单例/缓存 ====================

@lru_cache(maxsize=1)
def _get_chat_model() -> ChatOpenAI:
    """
    获取大模型聊天实例（单例）
    
    使用 lru_cache 确保只创建一次实例。
    
    Returns:
        ChatOpenAI: 大模型聊天实例
    """
    logger.info("初始化 ChatOpenAI 实例")
    return ChatOpenAI(
        api_key=os.getenv("DASHSCOPE_KEY"),
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        model=os.getenv("TONGYI_MODEL"),
    )


@lru_cache(maxsize=1)
def _get_rag_prompt() -> ChatPromptTemplate:
    """
    获取 RAG 模式的 Prompt 模板（单例）
    
    当检索到相关工作记录时使用此模板。
    """
    return ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的工作助手，能够根据用户的工作记录回答问题。

            **你的职责：**
            1. 根据提供的工作记录上下文，准确回答用户的问题
            2. 如果上下文中包含相关信息，请基于这些信息进行回答
            3. 如果上下文信息不足以完整回答问题，可以结合上下文给出部分回答，并说明哪些信息不在记录中
            4. 回答要简洁、准确、有条理
            
            **注意事项：**
            - 优先使用工作记录中的信息
            - 如果用户问的内容与工作记录无关，可以正常回答
            - 保持友好、专业的语气"""
         ),
        # 对话历史
        MessagesPlaceholder(variable_name="history"),
        # 检索到的上下文
        ("system", "**相关工作记录：**\n{context}"),
        ("human", "{input}"),
    ])


@lru_cache(maxsize=1)
def _get_general_prompt() -> ChatPromptTemplate:
    """
    获取通用对话的 Prompt 模板（单例）
    
    当没有检索到相关记录时使用此模板。
    """
    return ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的聊天助手，能够使用通俗易懂的语言回答用户的问题。

            **你的职责：**
            1. 回答用户的各种问题
            2. 如果用户询问工作相关的内容，但你没有相关记录，请友好地告知
            3. 遇到无法回答的问题，能够告知用户并给予一定的友好建议
            
            **注意事项：**
            - 保持友好、专业的语气
            - 回答要简洁、准确"""
         ),
        # 对话历史
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])


# ==================== 会话历史管理 ====================

# 存储历史会话记录，后续用于上下文理解。生产环境中，使用数据库存储。
chat_memory_history: Dict[str, ChatMessageHistory] = {}


def _get_message_history(session_id: str) -> ChatMessageHistory:
    """
    获取会话历史记录
    
    Args:
        session_id: 会话 ID
        
    Returns:
        ChatMessageHistory: 会话历史记录
    """
    message_history = chat_memory_history.get(session_id)
    if message_history is None:
        message_history = ChatMessageHistory()
        chat_memory_history[session_id] = message_history
    return message_history


def clear_session_history(session_id: str) -> None:
    """
    清除指定会话的历史记录
    
    Args:
        session_id: 会话 ID
    """
    if session_id in chat_memory_history:
        del chat_memory_history[session_id]
        logger.info(f"已清除会话历史: {session_id}")


# ==================== RAG 检索 ====================

def _retrieve_relevant_documents(
        query: str,
        date_range: Optional[Tuple[date, date]] = None,
        report_type: Optional[str] = None
) -> List[Document]:
    """
    从向量数据库检索相关文档，支持日期和报告类型过滤
    
    Args:
        query: 用户查询
        date_range: 可选的日期范围 (start_date, end_date)
        report_type: 可选的报告类型（daily/weekly/None）
        
    Returns:
        List[Document]: 相关文档列表
    """
    try:
        start_date, end_date = date_range if date_range else (None, None)

        # 构建日志信息
        filter_info = []
        if date_range:
            filter_info.append(f"日期: {start_date} ~ {end_date}")
        if report_type:
            filter_info.append(f"类型: {report_type}")
        filter_str = f"({', '.join(filter_info)})" if filter_info else "(无过滤)"

        logger.info(f"开始检索相关文档: {query[:30]}... {filter_str}")

        documents = search_similar_documents(
            query,
            k=RAG_TOP_K,
            start_date=start_date,
            end_date=end_date,
            report_type=report_type
        )

        logger.info(f"检索到 {len(documents)} 条相关文档")
        return documents
    except Exception as e:
        logger.warning(f"文档检索失败，将使用通用对话模式: {e}")
        return []


def _format_context(documents: List[Document]) -> str:
    """
    将检索到的文档格式化为上下文字符串
    
    Args:
        documents: 文档列表
        
    Returns:
        str: 格式化的上下文
    """
    if not documents:
        return ""

    context_parts = []
    for i, doc in enumerate(documents, 1):
        # 提取元数据
        metadata = doc.metadata

        # 日期范围
        date_info = ""
        if metadata.get("start_date") and metadata.get("end_date"):
            start = metadata["start_date"]
            end = metadata["end_date"]
            if start == end:
                date_info = f"[{start}]"
            else:
                date_info = f"[{start} ~ {end}]"

        # 报告类型
        report_type = metadata.get("report_type", "")
        type_label = {"daily": "日报", "weekly": "周报"}.get(report_type, "")
        if type_label:
            date_info = f"{date_info}({type_label})"

        context_parts.append(f"【记录 {i}】{date_info}\n{doc.page_content}")

    return "\n\n".join(context_parts)


# ==================== 主要 API ====================

def chat_with_llm(question: str, session_id: str):
    """
    与大模型进行聊天，支持 RAG 检索增强
    
    工作流程：
    1. 解析问题中的日期范围和报告类型
    2. 检索向量数据库，查找相关工作记录（支持日期和类型过滤）
    3. 如果找到相关记录 → 使用 RAG 模式，将记录作为上下文
    4. 如果没有找到 → 使用通用对话模式
    5. 流式输出回复
    
    Args:
        question: 用户问题
        session_id: 会话 ID
        
    Yields:
        流式输出的回复内容
    """
    logger.info(f"收到用户问题: {question[:50]}... (session: {session_id})")

    # 获取缓存的 ChatModel
    chat_model = _get_chat_model()

    # Step 1: 解析日期范围和报告类型
    query_info = extract_query_info(question)

    # Step 2: 检索相关文档（带日期和类型过滤）
    documents = _retrieve_relevant_documents(
        question,
        date_range=query_info.date_range,
        report_type=query_info.report_type
    )

    # Step 2: 根据检索结果选择对话模式
    if documents:
        # RAG 模式：有相关文档
        logger.info("使用 RAG 模式回答")
        context = _format_context(documents)
        prompt = _get_rag_prompt()

        chain = prompt | chat_model

        llm = RunnableWithMessageHistory(
            runnable=chain,
            get_session_history=_get_message_history,
            input_messages_key="input",
            history_messages_key="history",
        )

        return llm.stream(
            {"input": question, "context": context},
            config=RunnableConfig(
                configurable={"session_id": session_id}
            ),
        )
    else:
        # 通用对话模式：没有相关文档
        logger.info("使用通用对话模式回答")
        prompt = _get_general_prompt()

        chain = prompt | chat_model

        llm = RunnableWithMessageHistory(
            runnable=chain,
            get_session_history=_get_message_history,
            input_messages_key="input",
            history_messages_key="history",
        )

        return llm.stream(
            {"input": question},
            config=RunnableConfig(
                configurable={"session_id": session_id}
            ),
        )


def chat_with_llm_sync(question: str, session_id: str) -> str:
    """
    与大模型进行聊天（同步版本，非流式）
    
    Args:
        question: 用户问题
        session_id: 会话 ID
        
    Returns:
        str: 完整的回复内容
    """
    response_parts = []
    for chunk in chat_with_llm(question, session_id):
        if hasattr(chunk, 'content') and chunk.content:
            response_parts.append(chunk.content)
    return "".join(response_parts)


# ==================== 日期提取 ====================

class QueryInfo(BaseModel):
    """查询信息结构（日期范围 + 报告类型）"""
    start_date: Optional[str] = Field(
        default=None,
        description="开始日期，格式为 YYYY-MM-DD，如果问题中没有时间相关的词则返回 null"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="结束日期，格式为 YYYY-MM-DD，如果问题中没有时间相关的词则返回 null"
    )
    has_date_reference: bool = Field(
        default=False,
        description="问题中是否包含时间相关的词（如：昨天、上周、12月1日等）"
    )
    report_type: Optional[str] = Field(
        default=None,
        description="报告类型：daily（日报）、weekly（周报）、null（不确定/同时检索）"
    )


@lru_cache(maxsize=1)
def _get_query_extraction_prompt() -> ChatPromptTemplate:
    """获取查询信息提取的 Prompt 模板（日期 + 报告类型）"""
    return ChatPromptTemplate.from_messages([
        ("system", """你是一个查询解析助手。你的任务是从用户问题中提取时间范围和报告类型，并以 JSON 格式返回结果。

            **当前日期信息：**
            - 今天是：{today}（{weekday}）
            
            **日期解析规则：**
            1. "今天" → 今天的日期
            2. "昨天" → 昨天的日期
            3. "前天" → 前天的日期
            4. "本周"/"这周" → 本周一 ~ 今天
            5. "上周" → 上周一 ~ 上周日
            6. "这个月"/"本月" → 本月1日 ~ 今天
            7. "上个月" → 上月1日 ~ 上月最后一天
            8. "周一"/"周二"等 → 如果今天还没到这一天，取上周的；否则取本周的
            9. "上周一"/"上周五"等 → 上周对应的日期
            10. "最近一周"/"最近7天" → 7天前 ~ 今天
            11. "最近一个月" → 30天前 ~ 今天
            12. 具体日期如"12月1日"/"12月1号" → 对应日期（年份默认为今年）
            13. 完整日期如"2025-12-01"/"2025年12月1日" → 对应日期
            
            **报告类型识别规则：**
            1. 明确提到"日报"、"每日"、"当天"、"那天做了什么" → report_type = "daily"
            2. 明确提到"周报"、"每周"、"周总结"、"一周总结" → report_type = "weekly"
            3. 提到"上周"、"本周"、"这周" 但没有明确说"日报" → report_type = "weekly"（倾向于周报）
            4. 提到具体某一天（如"周一"、"昨天"、"12月1日"）→ report_type = "daily"（倾向于日报）
            5. 不确定或者同时需要 → report_type = null
            
            **重要提示：**
            - 如果问题中没有任何时间相关的词，则 has_date_reference = false，start_date 和 end_date 返回 null
            - 所有日期格式统一为 YYYY-MM-DD
            - 如果是单个日期（如"昨天"），start_date 和 end_date 相同
            - report_type 只能是 "daily"、"weekly" 或 null
            
            请以 JSON 格式返回解析结果。"""),
        ("human", "{question}")
    ])


class ExtractedQueryInfo:
    """提取的查询信息"""

    def __init__(
            self,
            date_range: Optional[Tuple[date, date]] = None,
            report_type: Optional[str] = None
    ):
        self.date_range = date_range
        self.report_type = report_type


def extract_query_info(question: str) -> ExtractedQueryInfo:
    """
    使用大模型从用户问题中提取日期范围和报告类型
    
    Args:
        question: 用户问题
        
    Returns:
        ExtractedQueryInfo: 包含日期范围和报告类型的对象
    """
    try:
        logger.info(f"开始解析查询信息: {question[:50]}...")

        # 获取当前日期信息
        today = date.today()
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_names[today.weekday()]

        # 使用结构化输出
        chat_model = _get_chat_model()
        structured_llm = chat_model.with_structured_output(QueryInfo)

        prompt = _get_query_extraction_prompt()
        chain = prompt | structured_llm

        result: QueryInfo = chain.invoke({
            "today": today.strftime("%Y-%m-%d"),
            "weekday": weekday,
            "question": question
        })

        logger.info(f"查询解析结果: has_date={result.has_date_reference}, "
                    f"start={result.start_date}, end={result.end_date}, "
                    f"report_type={result.report_type}")

        # 解析日期范围
        date_range = None
        if result.has_date_reference and result.start_date and result.end_date:
            start = datetime.strptime(result.start_date, "%Y-%m-%d").date()
            end = datetime.strptime(result.end_date, "%Y-%m-%d").date()
            date_range = (start, end)
            logger.info(f"日期范围: {start} ~ {end}")
        else:
            logger.info("问题中没有时间相关的词，跳过日期过滤")

        # 报告类型
        report_type = result.report_type
        logger.info(f"报告类型: {report_type or '全部'}")

        return ExtractedQueryInfo(date_range=date_range, report_type=report_type)

    except Exception as e:
        logger.warning(f"查询解析失败，将不使用过滤: {e}")
        return ExtractedQueryInfo()


# 保留旧函数名以兼容
def extract_date_range(question: str) -> Optional[Tuple[date, date]]:
    """
    使用大模型从用户问题中提取日期范围（兼容旧接口）
    
    Args:
        question: 用户问题
        
    Returns:
        (start_date, end_date) 元组，如果问题中没有时间词则返回 None
    """
    info = extract_query_info(question)
    return info.date_range


# ==================== 工具函数 ====================

def clear_chat_model_cache() -> None:
    """清除 ChatModel 缓存，用于配置变更后重新初始化"""
    _get_chat_model.cache_clear()
    _get_rag_prompt.cache_clear()
    _get_general_prompt.cache_clear()
    _get_query_extraction_prompt.cache_clear()
    logger.info("已清除 ChatModel 和 Prompt 缓存")


def main():
    """测试查询信息提取"""
    test_questions = [
        "昨天的日报",
        "上周周报",
        "本周做了什么",
        "12月1日干了啥",
        "最近一个月的工作记录",
        "你好",
    ]

    for question in test_questions:
        print(f"\n问题: {question}")
        info = extract_query_info(question)
        print(f"  日期范围: {info.date_range}")
        print(f"  报告类型: {info.report_type}")


if __name__ == '__main__':
    main()
