"""
LLM RAG 服务

提供文档向量化和存储功能，用于后续的语义检索。

优化说明：
- 使用模块级单例管理 Milvus 连接和 Embedding 模型
- 延迟初始化：首次使用时创建，后续复用
- 添加连接健康检查和自动重连机制
- 使用线程锁确保线程安全
"""
import os
import logging
import threading
from datetime import date, datetime, timedelta
from typing import Optional

from langchain_milvus import Milvus
from pymilvus import connections, db
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from basic.embedding.custom_embeddings import CustomMultimodalEmbeddings
from dotenv import load_dotenv
from work_record_project.app.core import ReportType

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 配置（可从环境变量读取） ====================

MILVUS_URI = os.getenv("MILVUS_URI", "http://192.168.2.148:19530")
MILVUS_USER = os.getenv("MILVUS_USER", "root")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "Milvus")
MILVUS_DB_NAME = os.getenv("MILVUS_DB_NAME", "work_report")
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "daily_report")

EMBEDDING_API_BASE = os.getenv("EMBEDDING_API_BASE", "http://192.168.2.59:8000/v1")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "93e5f02e99061db3b6113e8db46a0fbd")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "multimodal-embedding-7b")

connection_args = {
    "uri": MILVUS_URI,
    "user": MILVUS_USER,
    "password": MILVUS_PASSWORD
}


# ==================== 单例管理 ====================

def _ensure_database_exists() -> None:
    """
    确保目标数据库存在（使用临时连接）
    """
    temp_alias = "milvus_temp"
    try:
        logger.info(f"检查数据库是否存在: {MILVUS_DB_NAME}")

        # 使用临时连接检查/创建数据库（带超时）
        connections.connect(alias=temp_alias, timeout=30, **connection_args)

        existing_dbs = db.list_database(using=temp_alias)
        logger.info(f"现有数据库列表: {existing_dbs}")

        if MILVUS_DB_NAME not in existing_dbs:
            db.create_database(MILVUS_DB_NAME, using=temp_alias)
            logger.info(f"✅ 创建数据库: {MILVUS_DB_NAME}")
        else:
            logger.info(f"数据库已存在: {MILVUS_DB_NAME}")

    except Exception as e:
        logger.error(f"数据库检查/创建失败: {e}", exc_info=True)
        raise
    finally:
        # 断开临时连接，因为 langchain 内部会进行Milvus 的连接
        if connections.has_connection(temp_alias):
            connections.disconnect(temp_alias)
            logger.debug("已断开临时连接")


class MilvusManager:
    """
    Milvus 连接管理器（线程安全单例）
    
    特性：
    - 延迟初始化：首次调用时创建连接
    - 连接复用：整个应用生命周期内复用同一连接
    - 线程安全：使用锁确保多线程环境下的安全
    - 自动重连：连接断开时自动重新建立
    """

    _instance: Optional['MilvusManager'] = None
    # 使用 RLock（可重入锁）， Lock（不可冲入的锁，如果一个线程获取之后，同一个线程在获取或导致等待） 避免 get_vectorstore 调用 get_embedding_model 时死锁
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._embedding_model: Optional[Embeddings] = None
        self._vectorstore: Optional[Milvus] = None
        self._connection_alias = 'milvus'
        self._initialized = True
        logger.info("MilvusManager 单例初始化完成")

    def get_embedding_model(self) -> Embeddings:
        """
        获取 Embedding 模型单例
        
        注意：此方法只在 get_vectorstore() 内部调用，已在锁保护下，无需额外加锁
        """
        if self._embedding_model is None:
            logger.info(f"初始化 Embedding 模型实例: {EMBEDDING_MODEL} @ {EMBEDDING_API_BASE}")
            try:
                self._embedding_model = CustomMultimodalEmbeddings(
                    api_base=EMBEDDING_API_BASE,
                    api_key=EMBEDDING_API_KEY,
                    model=EMBEDDING_MODEL,
                )
                logger.info("Embedding 模型实例创建成功")
            except Exception as e:
                logger.error(f"Embedding 模型创建失败: {e}", exc_info=True)
                raise
        return self._embedding_model

    def get_vectorstore(self) -> Milvus:
        """
        获取向量存储单例
        
        包含连接健康检查和自动重连机制。
        """
        # 使用双重检查锁定模式
        if self._vectorstore is None:
            with self._lock:
                if self._vectorstore is None:
                    # 确保数据库存在
                    _ensure_database_exists()

                    logger.info(f"初始化 Milvus 向量存储: {MILVUS_COLLECTION}")

                    # 先获取 embedding 模型
                    logger.info("获取 Embedding 模型...")
                    embedding_model = self.get_embedding_model()
                    logger.info(f"Embedding 模型获取成功: {type(embedding_model).__name__}")

                    # 构建带 db_name 和超时的连接参数
                    milvus_connection_args = {
                        **connection_args,
                        "db_name": MILVUS_DB_NAME,
                        "timeout": 30,  # 连接超时 30 秒
                    }
                    logger.info(f"Milvus 连接参数: uri={connection_args.get('uri')}, db_name={MILVUS_DB_NAME}")

                    try:
                        logger.info("开始创建 Milvus 向量存储实例...")

                        # 让 langchain_milvus 自己管理连接
                        self._vectorstore = Milvus(
                            collection_name=MILVUS_COLLECTION,
                            connection_args=milvus_connection_args,
                            auto_id=True,
                            embedding_function=embedding_model,
                            index_params={
                                "index_type": "IVF_FLAT",
                                "metric_type": "COSINE",
                                "params": {"nlist": 128}
                            },
                            search_params={
                                "metric_type": "COSINE",
                                "params": {"nprobe": 16}
                            },
                            drop_old=False,
                        )
                        logger.info("✅ Milvus 向量存储实例创建成功")
                    except Exception as e:
                        logger.error(f"❌ Milvus 向量存储创建失败: {e}", exc_info=True)
                        raise
        return self._vectorstore

    def reset(self) -> None:
        """
        重置所有实例
        
        用于配置变更或连接异常时的重置。
        """
        with self._lock:
            self._vectorstore = None
            self._embedding_model = None
            logger.info("MilvusManager 已重置")


# 全局管理器实例
_milvus_manager: Optional[MilvusManager] = None


def _get_milvus_manager() -> MilvusManager:
    """获取 Milvus 管理器单例"""
    global _milvus_manager
    if _milvus_manager is None:
        _milvus_manager = MilvusManager()
    return _milvus_manager


# ==================== 公开 API ====================

def embedding_with_llm(start_date: date, end_date: date, report: str, report_type: ReportType) -> None:
    """
    将文本向量化并存储到 Milvus
    
    使用单例管理的连接和模型，避免重复创建。
    
    Args:
        start_date: 报告开始日期
        end_date: 报告结束日期
        report: 要向量化的文本（Markdown 格式）
        report_type: 报告类型（daily 或 weekly）
    """
    logger.info(f"开始向量化存储，日期范围: {start_date} ~ {end_date}")
    logger.debug(f"输入文本长度: {len(report)} 字符")

    try:
        # 获取向量存储（使用单例）
        logger.info("获取 Milvus 向量存储实例...")
        manager = _get_milvus_manager()
        vectorstore = manager.get_vectorstore()
        logger.info("Milvus 向量存储实例获取成功")

        # Markdown 文档分割
        logger.info("开始 Markdown 文档分割...")
        headers_to_split_on = [
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]

        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            return_each_line=False,
        )

        docs = markdown_splitter.split_text(report)
        logger.info(f"Markdown 分割完成，得到 {len(docs)} 个文档块")

        # 检查是否有文档
        if not docs:
            logger.warning("Markdown 分割后没有文档，可能是文本中没有标题。跳过向量化。")
            return

        # 转换为 Document，添加元数据
        logger.info("转换为 Document 对象...")
        documents = [
            Document(
                page_content=doc.page_content,
                metadata={
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "create_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "report_type": report_type.value,
                }
            )
            for doc in docs
        ]
        logger.info(f"Document 转换完成，共 {len(documents)} 个文档")

        # 添加到向量存储（这一步会调用 Embedding 模型并写入 Milvus）
        logger.info("开始调用 Embedding 模型并写入 Milvus...")
        vectorstore.add_documents(documents)
        logger.info(f"✅ 成功添加 {len(documents)} 条文档到向量存储")

    except Exception as e:
        logger.error(f"❌ 向量化存储失败: {e}", exc_info=True)
        raise


def search_similar_documents(
        query: str, 
        k: int = 5, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        report_type: Optional[str] = None
) -> list:
    """
    语义搜索相似文档

    Args:
        query: 搜索查询
        k: 返回结果数量
        start_date: 报告开始日期
        end_date: 报告结束日期
        report_type: 报告类型过滤（daily/weekly/None 表示全部）

    Returns:
        相似文档列表
    """
    try:
        manager = _get_milvus_manager()
        vectorstore = manager.get_vectorstore()
        
        # 构建过滤条件
        filter_conditions = []
        
        # 日期过滤
        if start_date and end_date:
            filter_conditions.append(f'start_date >= "{start_date}"')
            filter_conditions.append(f'end_date <= "{end_date}"')
        
        # 报告类型过滤
        if report_type:
            filter_conditions.append(f'report_type == "{report_type}"')
        
        # 组合过滤条件
        filter_expr = " and ".join(filter_conditions) if filter_conditions else None
        
        if filter_expr:
            logger.info(f"检索过滤条件: {filter_expr}")

        results = vectorstore.similarity_search(
            query,
            k=k,
            expr=filter_expr
        )
        logger.info(f"搜索到 {len(results)} 条相关文档")
        return results
    except Exception as e:
        logger.error(f"语义搜索失败: {e}")
        raise


def reset_milvus_connection() -> None:
    """
    重置 Milvus 连接
    
    用于配置变更或连接异常后的手动重置。
    """
    manager = _get_milvus_manager()
    manager.reset()


def main():
    """
    主函数，用于测试 Milvus 连接和向量化存储
    """
    # 配置日志输出
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("开始测试 Milvus 连接和向量化存储")
    print("=" * 60)

    text = """
        ## 2025-12-01 工作日报
        
        ### 今日完成
        **产品工作**  
        - 城市大脑智能中枢：参与学习中心需求评审  
        
        **项目工作**  
        - 龙泉项目：完成登录模块基础框架搭建  
        
        **其它**  
        - 参加技术分享会  
        
        ### 风险问题  
        - 数据库选型尚未确定，可能影响后续开发进度  
        
        ### 次日计划  
        - 继续推进龙泉项目登录模块的开发工作  
        
        ---  
        **生成时间**: 2025-12-01
    """

    start_date = date.today()
    end_date = start_date + timedelta(1)

    print(f"\n日期范围: {start_date} ~ {end_date}")
    print(f"文本长度: {len(text)} 字符")
    print("-" * 60)

    try:
        embedding_with_llm(start_date, end_date, text, "daily")
        print("\n" + "=" * 60)
        print("✅ 测试完成")
        print("=" * 60)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ 测试失败: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
