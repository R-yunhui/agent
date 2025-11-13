"""
RAG 系统配置文件

集中管理所有 RAG 相关的配置参数，包括：
- Milvus 向量数据库配置
- Embedding 模型配置
- 文本切分配置
- 检索配置
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# ========== LLM 配置 ==========
class LLMConfig:
    """大语言模型配置"""
    API_BASE = os.getenv("OPENAI_API_BASE", "http://192.168.2.59:8000/v1")
    API_KEY = os.getenv("OPENAI_API_KEY", None)
    MODEL = os.getenv("OPENAI_MODEL", "qwen2.5-vl-72b-instruct")
    TEMPERATURE = 0.3
    MAX_TOKENS = 2000


# ========== Embedding 配置 ==========
class EmbeddingConfig:
    """向量化模型配置"""
    # OpenAI Embedding 配置
    API_BASE = os.getenv("OPENAI_API_BASE", "http://192.168.2.59:8000/v1/")
    API_KEY = os.getenv("OPENAI_API_KEY", None)
    MODEL = os.getenv("EMBEDDING_MODEL", "multimodal-embedding")

    # 向量维度（根据你的模型调整）
    DIMENSION = 1536


# ========== Milvus 配置 ==========
class MilvusConfig:
    """Milvus 向量数据库配置"""

    # 连接配置（请根据你的实际部署修改）
    HOST = os.getenv("MILVUS_HOST", "192.168.2.148")
    PORT = os.getenv("MILVUS_PORT", "19530")

    # 认证配置（如果启用了认证）
    USER = os.getenv("MILVUS_USER", "root")
    PASSWORD = os.getenv("MILVUS_PASSWORD", "Milvus")

    # 集合（Collection）配置
    COLLECTION_NAME = "langchain_demo_knowledge_base"

    # 数据库
    DB_NAME = "langchain_demo_knowledge_db"

    # 索引配置
    INDEX_TYPE = "IVF_FLAT"  # 索引类型：IVF_FLAT, IVF_SQ8, HNSW 等
    METRIC_TYPE = "L2"  # 距离度量：L2（欧氏距离）、IP（内积）、COSINE（余弦相似度）
    INDEX_PARAMS = {
        "nlist": 128  # IVF 索引的聚类中心数量
    }

    # 检索配置
    SEARCH_PARAMS = {
        "nprobe": 10  # 检索时要查询的聚类中心数量
    }

    # 其他配置
    TOP_K = 4  # 默认检索的文档数量

    @classmethod
    def get_connection_args(cls) -> dict:
        """获取 Milvus 连接参数"""
        args = {
            "uri": "http://" + cls.HOST + ":" + cls.PORT,
        }

        # 如果配置了用户名和密码，添加到连接参数
        if cls.USER and cls.PASSWORD:
            args["user"] = cls.USER
            args["password"] = cls.PASSWORD

        return args


# ========== 文本切分配置 ==========
class TextSplitterConfig:
    """文本切分器配置"""

    # 切分块大小（字符数）
    CHUNK_SIZE = 500

    # 块之间的重叠大小（字符数）
    # 重叠可以保证上下文的连续性
    CHUNK_OVERLAP = 50

    # 分隔符优先级（从高到低）
    SEPARATORS = [
        "\n\n",  # 段落
        "\n",  # 行
        "。",  # 中文句号
        "！",  # 中文感叹号
        "？",  # 中文问号
        "；",  # 中文分号
        "，",  # 中文逗号
        " ",  # 空格
        ""  # 字符级别
    ]


# ========== 文档加载配置 ==========
class DocumentConfig:
    """文档加载配置"""

    # 文档目录
    DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "documents")

    # 支持的文件类型
    SUPPORTED_EXTENSIONS = [".txt", ".md", ".pdf", ".docx"]

    # 文档元数据字段
    METADATA_FIELDS = ["source", "page", "category"]


# ========== RAG 检索配置 ==========
class RAGConfig:
    """RAG 检索和生成配置"""

    # 检索配置
    RETRIEVAL_TOP_K = 4  # 检索文档数量
    SCORE_THRESHOLD = 0.5  # 相似度阈值（0-1，越高越严格）

    # 检索模式
    SEARCH_TYPE = "similarity"  # similarity, mmr, similarity_score_threshold

    # MMR（最大边际相关性）配置
    MMR_FETCH_K = 20  # MMR 候选文档数量
    MMR_LAMBDA = 0.5  # 多样性参数（0: 最多样，1: 最相关）

    # 提示词模板
    SYSTEM_TEMPLATE = """你是一个专业的问答助手，请根据提供的上下文信息回答用户的问题。

注意事项：
1. 如果上下文中包含答案，请直接引用相关内容
2. 如果上下文中没有足够信息，请明确告知用户
3. 回答要准确、简洁、有条理
4. 可以适当扩展说明，但不要偏离上下文内容

上下文信息：
{context}
"""

    HUMAN_TEMPLATE = """问题：{question}

请基于上述上下文信息回答问题。"""


# ========== 辅助函数 ==========

def print_config_summary():
    """打印配置摘要"""
    print("=" * 80)
    print("📋 RAG 系统配置摘要")
    print("=" * 80)

    print("\n🤖 LLM 配置：")
    print(f"   API Base: {LLMConfig.API_BASE}")
    print(f"   Model: {LLMConfig.MODEL}")
    print(f"   Temperature: {LLMConfig.TEMPERATURE}")

    print("\n🔢 Embedding 配置：")
    print(f"   Model: {EmbeddingConfig.MODEL}")
    print(f"   Dimension: {EmbeddingConfig.DIMENSION}")

    print("\n🗄️  Milvus 配置：")
    print(f"   Host: {MilvusConfig.HOST}:{MilvusConfig.PORT}")
    print(f"   Collection: {MilvusConfig.COLLECTION_NAME}")
    print(f"   Index Type: {MilvusConfig.INDEX_TYPE}")
    print(f"   Metric Type: {MilvusConfig.METRIC_TYPE}")
    print(f"   Top K: {MilvusConfig.TOP_K}")

    print("\n✂️  文本切分配置：")
    print(f"   Chunk Size: {TextSplitterConfig.CHUNK_SIZE}")
    print(f"   Chunk Overlap: {TextSplitterConfig.CHUNK_OVERLAP}")

    print("\n📂 文档配置：")
    print(f"   Documents Dir: {DocumentConfig.DOCUMENTS_DIR}")
    print(f"   Supported: {', '.join(DocumentConfig.SUPPORTED_EXTENSIONS)}")

    print("\n🔍 RAG 检索配置：")
    print(f"   Top K: {RAGConfig.RETRIEVAL_TOP_K}")
    print(f"   Search Type: {RAGConfig.SEARCH_TYPE}")
    print(f"   Score Threshold: {RAGConfig.SCORE_THRESHOLD}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 测试配置
    print_config_summary()
