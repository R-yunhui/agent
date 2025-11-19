# mem 框架，用于大模型记忆管理 简单示例
import json

from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from mem0 import Memory
from mem0.configs.base import MemoryConfig, EmbedderConfig, VectorStoreConfig
from mem0.llms.configs import LlmConfig

from basic.embedding.custom_embeddings import CustomMultimodalEmbeddings

# 加载 env
load_dotenv()

VECTOR_STORE_SAVE_DIR = "qdrant"

llm = ChatOpenAI(
    model=os.getenv("OPENAI_CHAT_MODEL"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7,
    max_retries=3,
    max_tokens=4096
)

embedding = CustomMultimodalEmbeddings(
    api_base=os.getenv("OPENAI_API_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("EMBEDDING_MODEL"),
)


def main():
    # 初始化 mem 客户端
    m = Memory(
        config=MemoryConfig(
            # 配置大语言模型
            llm=LlmConfig(
                provider="langchain",
                config={
                    "model": llm
                }
            ),
            # 配置 embedding 模型
            embedder=EmbedderConfig(
                provider="langchain",
                config={
                    "model": embedding
                }
            ),
            # 配置向量存储地址
            # qdrant 默认的 cosine 相似度，范围 [-1, 1]，分数越高，相似度越高
            vector_store=VectorStoreConfig(
                provider="qdrant",
                config={
                    "embedding_model_dims": 3584,  # 匹配您的 embedding 模型维度
                    "collection_name": "mem0",
                    "path": os.path.join(os.getcwd(), VECTOR_STORE_SAVE_DIR)  # mem0 默认使用本地存储向量，路径为 /tmp/qdrant
                }
            )
        )
    )

    messages = [
        {"role": "user", "content": "我喜欢篮球和游戏."},
        {"role": "assistant", "content": "我会记住你喜欢篮球和游戏."},
        {"role": "user", "content": "我喜欢足球."},
        {"role": "assistant", "content": "我会记住你喜欢足球."},
        {"role": "user", "content": "我今年25岁."},
        {"role": "assistant", "content": "我会记住你今年25岁."},
        {"role": "user", "content": "我来自中国."},
        {"role": "assistant", "content": "我会记住你来自中国."},
        {"role": "user", "content": "我是一个学生."},
        {"role": "assistant", "content": "我会记住你是一个学生."},
        {"role": "user", "content": "我叫张哥"},
        {"role": "assistant", "content": "我会记住你叫张哥."}
    ]

    m.add(messages, user_id="alex")

    results = m.search("我是谁?", user_id="alex", threshold=0.2, limit=3)
    print(json.dumps(results, ensure_ascii=False))
    results = m.search("我来自哪里?", user_id="alex", threshold=0.2, limit=3)
    print(json.dumps(results, ensure_ascii=False))
    results = m.search("我喜欢什么运动?", user_id="alex", threshold=0.2, limit=3)
    print(json.dumps(results, ensure_ascii=False))
    results = m.search("张哥喜欢什么运动?", user_id="alex", threshold=0.2, limit=3)
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    # 创建存储目录
    os.makedirs(os.path.join(os.getcwd(), VECTOR_STORE_SAVE_DIR), exist_ok=True)
    main()
