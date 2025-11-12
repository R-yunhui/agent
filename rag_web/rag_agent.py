from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig, RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.embeddings import Embeddings
from langchain_openai.embeddings import OpenAIEmbeddings
from pymilvus import connections, db
from langchain_milvus import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter

import os
import yaml
from typing import Dict, Iterator
from _collections_abc import Iterator as ABCIterator

from basic.embedding.custom_embeddings import CustomMultimodalEmbeddings


# ============================================================
# 1. 加载配置文件
# ============================================================

def load_config():
    """加载 YAML 配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "config/config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

# 存储历史会话记录，后续用于上下文理解。生产环境中，使用数据库存储。
chat_memory_history: Dict[str, ChatMessageHistory] = {}

connection_args = {
    "uri": f"http://{config['milvus']['host']}:{config['milvus']['port']}",
    "user": config["milvus"]["user"],
    "password": config["milvus"]["password"]
}


def chat_with_memory(user_question: str, session_id: str) -> ABCIterator:
    """
    与OpenAI模型进行一次对话，返回模型的回复。
    该函数会记住之前的对话历史，用于上下文理解。

    :param user_question: 用户的问题或指令
    :param session_id: 会话ID，用于区分不同的对话历史
    :return: 模型的回复内容（流式）
    """
    try:
        # 1.先通过 rag 进行检索
        vectorstore = create_vector_store()

        vectorstore_results = vectorstore.similarity_search_with_score(
            query=user_question,
            k=config["rag"]["retrieval_top_k"],
        )

        message_history = create_chat_with_memory()

        if vectorstore_results is None or len(vectorstore_results) == 0:
            print("没有检索到相关文档, 直接使用大模型进行回复")
        else:
            print(f"检索到 {len(vectorstore_results)} 个相关文档")
            contents = []
            for result in vectorstore_results:
                document, score = result
                print(f"  - 相似度: {score:.4f}, 内容: {document.page_content[:100]}...")
                # 只使用相似度高于阈值的文档
                if score >= config["rag"]["similarity_threshold"]:
                    contents.append(document.page_content)

            if contents:
                # 将检索到的文档内容添加到用户问题中
                user_question = f"""
                    请根据以下文档回答用户的问题：

                    {chr(10).join(f"文档{i + 1}: {content}" for i, content in enumerate(contents))}

                    用户问题：{user_question}

                    请基于以上文档内容进行回答，如果文档中没有相关信息，请说明。
                """
                print(f"已将检索到的 {len(contents)} 个文档添加到提示词中")

        return message_history.stream(
            {"user_question": user_question},
            config=RunnableConfig(configurable={"session_id": session_id})
        )

    except Exception as e:
        print(f"对话过程中出错: {str(e)}")
        # 如果检索失败，直接使用大模型
        message_history = create_chat_with_memory()
        return message_history.stream(
            {"user_question": user_question},
            config=RunnableConfig(configurable={"session_id": session_id})
        )


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

    :param path: 文件路径，用于指定要处理的文件目录
    :param session_id: 会话ID，用于区分不同的对话历史
    :return: 向量存储对象
    """
    print(f"用户: {session_id}, 开始处理文件目录: {path}")
    if not os.path.isdir(path):
        raise FileNotFoundError(f"文件目录 {path} 不存在")

    file_list = os.listdir(path)
    if not file_list:
        raise FileNotFoundError(f"目录 {path} 下没有文件")

    documents = []
    for file in file_list:
        # 支持多种文件格式
        file_path = os.path.join(path, file)
        if not os.path.isfile(file_path):
            continue

        # 支持 .txt 文件
        if file.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():  # 只添加非空内容
                        documents.append(content)
            except Exception as e:
                print(f"读取文件 {file} 时出错: {e}")
                continue

        # 可以扩展支持其他文件格式
        # elif file.endswith(".pdf"):
        #     # 处理 PDF 文件
        #     pass
        # elif file.endswith(".docx"):
        #     # 处理 Word 文件
        #     pass

    if not documents:
        raise ValueError(f"目录 {path} 下没有可处理的文本内容")

    print(f"共读取 {len(documents)} 个文档")

    # 使用文本分割器将长文档分割成小块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["text_splitter"]["chunk_size"],
        chunk_overlap=config["text_splitter"]["chunk_overlap"],
        separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ", ""],
    )

    split_documents = []
    for doc in documents:
        splits = text_splitter.split_text(doc)
        split_documents.extend(splits)

    print(f"文档分割后共 {len(split_documents)} 个文本块")

    # langchain 内部会自己创建和管理 milvus 连接
    # from_texts 会自动完成：文本 -> 向量化 -> 存储
    embeddings = get_embedding_model()
    try:
        vectorstore = Milvus.from_texts(
            texts=split_documents,
            embedding=embeddings,
            collection_name=config["milvus"]["collection_name"],
            connection_args={
                **connection_args,
                "db_name": config["milvus"]["db_name"],
            },
            drop_old=True  # 如果集合存在则删除，重新创建
        )

        print(f"✅ 成功存储 {len(split_documents)} 个文档块到向量数据库")

    except Exception as e:
        print(f"❌ 向量数据库存储失败: {e}")
        raise
    finally:
        # 断开连接
        connections.disconnect("default")

    return vectorstore


def create_vector_store() -> Milvus:
    """
    创建向量存储
    :return: 向量存储对象
    """
    try:
        db_name = config["milvus"]["db_name"]

        # 先检查数据库是否存在
        if not check_data_base_exists(db_name):
            raise ConnectionError("Milvus 数据库不存在")

        # langchain 内部默认会进行 milvus 的连接
        vectorstore = Milvus(
            collection_name=config["milvus"]["collection_name"],
            connection_args={
                **connection_args,
                "db_name": db_name,
            },
            embedding_function=get_embedding_model(),
        )

        return vectorstore
    except Exception as e:
        print(f"创建向量存储失败: {str(e)}")
        print("将使用不带 RAG 的模式进行对话")
        raise


def check_data_base_exists(db_name: str) -> bool:
    try:
        connections.connect(
            alias="default",
            **connection_args
        )

        database_list = db.list_database()
        if db_name in database_list:
            print(f"数据库 {db_name} 已存在")
        else:
            db.create_database(db_name)
            print(f"数据库 {db_name} 创建成功")
        return True
    except Exception as e:
        print(f"检查 Milvus 数据库是否存在失败: {str(e)}")
        return False
    finally:
        # 关闭建立的连接
        connections.disconnect("default")


def get_embedding_model() -> Embeddings:
    """
    获取 Embedding 模型实例

    :return: Embedding 模型对象
    """
    return CustomMultimodalEmbeddings(
        api_base=config["embedding"]["api_base"],
        api_key=config["embedding"]["api_key"],
        model=config["embedding"]["model"],
    )


def main():
    """主函数，用于测试"""
    session_id = "test_001"

    # 测试文件处理
    path = os.path.join(os.path.dirname(__file__), "uploads")
    try:
        vectorstore = rag_execute_with_file(path, session_id)
        print("✅ 向量存储创建成功")

        results_with_scores = vectorstore.similarity_search_with_score("如何从Java转换到Python的学习", 3)
        if results_with_scores:
            for j, (doc, score) in enumerate(results_with_scores, 1):
                print(f"\n  结果 {j}:")
                print(f"  📊 相似度分数: {score:.4f}")
                print(f"  📄 内容: {doc.page_content}")
    except Exception as e:
        print(f"❌ 错误: {e}")

    # 测试对话
    # user_questions = ["你好，请介绍一下自己"]
    # for user_question in user_questions:
    #     print(f"\n用户: {user_question}")
    #     print("AI: ", end="")
    #     response = chat_with_memory(user_question, session_id)
    #     for chunk in response:
    #         if hasattr(chunk, 'content'):
    #             print(chunk.content, end="", flush=True)
    #     print("\n")


if __name__ == "__main__":
    main()
