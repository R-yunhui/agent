from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig, RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import MessagesPlaceholder
from _collections_abc import Iterator
from langchain_core.runnables.utils import Output
from basic.embedding.custom_embeddings import CustomMultimodalEmbeddings
from langchain_core.embeddings import Embeddings
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility, db
from langchain_milvus import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter

import os

import yaml
from typing import Dict

from langchain_openai.chat_models.base import BaseChatOpenAI

from config.llm_config import EmbeddingConfig, LLMConfig, RAGConfig, MilvusConfig, TextSplitterConfig, DocumentConfig


# ============================================================
# 1. 加载配置文件
# ============================================================

def load_config():
    """加载 YAML 配置文件"""
    config_path = os.path.join(os.getcwd(), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

# 存储历史会话记录，后续用于上下文理解。生产环境中，使用数据库存储。
chat_memory_history: Dict[str, ChatMessageHistory] = {}


def chat_with_memory(user_question: str, session_id: str) -> Iterator[Output]:
    """
    与OpenAI模型进行一次对话，返回模型的回复。
    该函数会记住之前的对话历史，用于上下文理解。

    :param user_question: 用户的问题或指令
    :param session_id: 会话ID，用于区分不同的对话历史
    :return: 模型的回复内容
    """
    # 1.先通过 rag 进行检索
    vectorstore = create_vector_store()
    vectorstore_results = vectorstore.similarity_search_with_score(
        query=user_question,
        k=RAGConfig.RETRIEVAL_TOP_K,
    )

    message_history = create_chat_with_memory()

    if vectorstore_results is None or len(vectorstore_results) == 0:
        print("没有检索到相关文档, 直接使用大模型进行回复")
    else:
        print(f"检索到 {len(vectorstore_results)} 个相关文档")
        contents = []
        for result in vectorstore_results:
            document, score = result
            contents.append(document.page_content)
        else:
            user_question = f"""
                        请根据以下文档回答用户的问题：
                        {contents}
                        用户问题：{user_question}
                        """
            print(f"最新的用户问题: {user_question}")

    return message_history.stream({"user_question": user_question}, config=RunnableConfig(
        configurable={"session_id": session_id}
    ))


def create_chat_with_memory() -> RunnableWithMessageHistory:
    """创建一个可记忆历史的聊天函数"""
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", config["prompts"]["system"]),
        # 对话历史
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_question}"),
    ])

    llm = get_large_model()
    runnable = prompt_template | llm

    message_history = RunnableWithMessageHistory(
        runnable=runnable,
        get_session_history=get_memory_history,
        input_messages_key="user_question",
        history_messages_key="history",
    )

    return message_history


def get_memory_history(session_id: str) -> ChatMessageHistory:
    """
    获取会话历史记录

    :param session_id: 会话ID，用于唯一标识一个会话
    :return: 会话历史记录对象，包含该会话的所有消息
    """
    memory_history = chat_memory_history.get(session_id)
    if not memory_history:
        memory_history = ChatMessageHistory()
        chat_memory_history[session_id] = memory_history
    return memory_history


def get_large_model() -> ChatOpenAI:
    """获取大模型实例"""
    return ChatOpenAI(
        base_url=config["llm"]["base_url"],
        api_key=config["llm"]["api_key"],
        model=config["llm"]["model"],
        temperature=config["llm"]["temperature"],
        max_tokens=config["llm"]["max_tokens"],
    )


def rag_execute_with_file(path: str, session_id: str) -> Milvus:
    """
    执行RAG模型的一次对话，返回模型的回复。

    :param path: 文件路径，用于指定要处理的文件
    :param session_id: 会话ID，用于区分不同的对话历史
    :return: 模型的回复内容
    """
    print(f"用户: {session_id}, 开始处理文件目录: {path}")
    if not os.path.isdir(path):
        raise FileNotFoundError(f"文件目录 {path} 不存在")

    file_list = os.listdir(path)
    if not file_list:
        raise FileNotFoundError(f"目录 {path} 下没有文件")

    documents = []
    for file in file_list:
        if not file.endswith(".txt"):
            continue

        try:
            with open(os.path.join(path, file), "r", encoding="utf-8") as f:
                for line in f:
                    documents.append(line)
        except Exception as e:
            print(f"读取文件 {file} 时出错: {e}")
            continue

    # langchain 内部会自己创建和管理 milvus 链接，自己创建 connection
    # from_texts 会自动完成：文本 -> 向量化 -> 存储
    embeddings = get_embedding_model()
    vectorstore = Milvus.from_texts(
        texts=documents,
        embedding=embeddings,
        collection_name=MilvusConfig.COLLECTION_NAME,
        connection_args={
            **MilvusConfig.get_connection_args(),
            "db_name": MilvusConfig.DB_NAME,
        },
        drop_old=True  # 如果集合存在则删除，测试使用
    )

    print(f"✅ 成功存储 {len(documents)} 个文档到向量数据库")

    # 断开连接
    connections.disconnect("default")
    return vectorstore


def create_vector_store():
    """
    创建向量存储
    :return: 向量存储对象
    """
    return Milvus(
        collection_name=MilvusConfig.COLLECTION_NAME,
        connection_args={
            **MilvusConfig.get_connection_args(),
            "db_name": MilvusConfig.DB_NAME,
        },
        embedding_function=get_embedding_model(),
    )


def get_embedding_model() -> Embeddings:
    """
    获取自定义多模态嵌入模型实例

    :return: 自定义多模态嵌入模型对象
    """
    return CustomMultimodalEmbeddings(
        api_base=EmbeddingConfig.API_BASE,
        api_key=EmbeddingConfig.API_KEY,
        model=EmbeddingConfig.MODEL,
        batch_size=5
    )


def main():
    """主函数，用于测试"""
    session_id = "001"
    user_questions = ["python在深度学习领域可以干什么？"]
    for user_question in user_questions:
        response = chat_with_memory(user_question, session_id)
        for chunk in response:
            print(chunk.content, end="")
        else:
            print("\n")

    # path = os.path.join(os.getcwd(), "doc")
    # vectorstore = rag_execute_with_file(path, session_id)
    # if not vectorstore:
    #     raise Exception("向量存储创建失败")
    # else:
    #     print("向量存储创建成功")
    #     # 进行检索测试
    #     results_with_scores = vectorstore.similarity_search_with_score(
    #         query="深度学习和神经网络",
    #         k=3
    #     )
    #
    #     print(f"检索到的结果数量: {len(results_with_scores)}")
    #     for j, (doc, score) in enumerate(results_with_scores, 1):
    #         print(f"\n  结果 {j}:")
    #         print(f"  📊 相似度分数: {score:.4f}")
    #         print(f"  📄 内容: {doc.page_content}")


if __name__ == "__main__":
    main()
