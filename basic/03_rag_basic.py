from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility, db
from langchain_milvus import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.llm_config import MilvusConfig, EmbeddingConfig, TextSplitterConfig
from embedding.custom_embeddings import CustomMultimodalEmbeddings


# ========== Milvus 连接测试 ==========

def test_milvus_connection():
    """测试 Milvus 连接"""
    print("\n🔌 测试 Milvus 连接")
    print("-" * 60)
    connection_args = MilvusConfig.get_connection_args()
    try:
        print(f"连接信息: {connection_args['uri']}")

        # 尝试连接
        connections.connect(
            alias="default",
            **connection_args
        )

        print("✅ Milvus 连接成功！")

        # 断开连接
        connections.disconnect("default")
        return True

    except Exception as e:
        print(f"❌ Milvus 连接失败: {e}")
        print("\n请检查：")
        print("  1. Milvus 是否正在运行")
        print("  2. config.py 中的连接配置是否正确")
        print(f"  3. 能否访问 {connection_args['uri']}")
        return False


# ========== 向量存储示例 ==========

def create_vector_store():
    """
    创建向量存储并插入示例数据
    
    流程：
    1. 初始化 Embedding 模型
    2. 准备示例文本数据
    3. 使用文本切分器处理长文本
    4. 创建/连接 Milvus 向量库
    5. 将文本向量化并存储
    """
    print("\n📦 创建向量存储")
    print("=" * 80)

    # 步骤1: 初始化 Embedding 模型
    print("\n步骤1: 初始化 Embedding 模型")
    print("-" * 60)
    embeddings = CustomMultimodalEmbeddings(
        api_base=EmbeddingConfig.API_BASE,
        api_key=EmbeddingConfig.API_KEY,
        model=EmbeddingConfig.MODEL,
        batch_size=5
    )

    # 步骤2: 准备示例文本数据
    print("\n步骤2: 准备示例文本数据")
    print("-" * 60)

    # 这里使用一些关于 Python 和 AI 的示例文本
    documents = [
        "Python是一种高级编程语言，由Guido van Rossum于1991年首次发布。它以简洁易读的语法而闻名，适合初学者学习编程。",
        "机器学习是人工智能的一个分支，它使计算机能够从数据中学习并做出决策，而无需明确编程。常见的机器学习算法包括决策树、神经网络和支持向量机。",
        "向量数据库是一种专门用于存储和检索高维向量的数据库。在 RAG（检索增强生成）系统中，向量数据库用于快速查找与查询最相似的文档片段。",
        "LangChain是一个用于开发由语言模型驱动的应用程序的框架。它提供了标准接口、外部集成和端到端链，简化了 LLM 应用的开发。",
        "Milvus是一个开源的向量数据库，专为处理大规模向量数据而设计。它支持多种索引类型和相似度度量，可以高效地进行向量检索。",
        "深度学习是机器学习的一个子领域，使用多层神经网络来学习数据的层次表示。它在图像识别、自然语言处理等领域取得了突破性进展。",
        "自然语言处理(NLP)是人工智能的一个分支，专注于使计算机能够理解、解释和生成人类语言。常见的NLP任务包括文本分类、命名实体识别和机器翻译。",
        "Transformer是一种深度学习架构，最初由Google在2017年提出。它使用自注意力机制，在序列建模任务中表现出色，是现代大语言模型的基础。"
    ]

    print(f"准备了 {len(documents)} 个示例文档")
    for i, doc in enumerate(documents, 1):
        print(f"  文档{i}: {doc[:50]}...")

    # 步骤3: 使用文本切分器（这里的示例文档较短，不需要切分，但展示用法）
    print("\n步骤3: 初始化文本切分器")
    print("-" * 60)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=TextSplitterConfig.CHUNK_SIZE,
        chunk_overlap=TextSplitterConfig.CHUNK_OVERLAP,
        separators=TextSplitterConfig.SEPARATORS
    )
    print(f"切分配置: chunk_size={TextSplitterConfig.CHUNK_SIZE}, overlap={TextSplitterConfig.CHUNK_OVERLAP}")

    # 步骤4: 连接 Milvus 并创建向量存储
    print("\n步骤4: 创建 Milvus 向量存储")
    print("-" * 60)

    try:
        # ✅ 1. 连接 Milvus
        connection_args = MilvusConfig.get_connection_args()
        # 建立一个临时链接进行测试
        using = 'temp'
        connections.connect(
            alias=using,
            **connection_args
        )

        # ✅ 2. 检查并创建数据库
        db_name = MilvusConfig.DB_NAME
        data_base_list = db.list_database(using=using, timeout=5000)
        if db_name not in data_base_list:  # 简化判断
            db.create_database(db_name, using=using)
            print(f"✅ 数据库 '{db_name}' 创建成功")
        else:
            print(f"ℹ️  数据库 '{db_name}' 已经存在.")

        # ✅ 4. 检查集合是否存在
        collection_name = MilvusConfig.COLLECTION_NAME
        if utility.has_collection(collection_name, using=using):
            print(f"⚠️  集合 '{collection_name}' 已经存在.")

        # 关闭这个临时链接
        connections.disconnect("temp")
        print(f"关闭已经建立的临时连接 temp")

        # ✅ 5. 创建向量存储
        print(f"\n步骤5: 将文档向量化并存储到 Milvus")
        print("-" * 60)

        # langchain 内部会自己创建和管理 milvus 链接，自己创建 connection
        # 创建向量存储并插入文档
        # from_texts 会自动完成：文本 -> 向量化 -> 存储
        vectorstore = Milvus.from_texts(
            texts=documents,
            embedding=embeddings,
            collection_name=collection_name,
            connection_args={
                **connection_args,
                "db_name": db_name,
            },
            drop_old=True  # 如果集合存在则删除，测试使用
        )

        print(f"✅ 成功存储 {len(documents)} 个文档到向量数据库")

        # ✅ 6. 断开连接
        connections.disconnect("default")  # ⚠️ 使用 alias，不是 db_name

        return vectorstore

    except Exception as e:
        print(f"❌ 创建向量存储失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ========== 向量查询示例 ==========

def query_vector_store():
    """
    从向量存储中查询相似文档
    
    流程：
    1. 连接到已存在的向量存储
    2. 执行相似度搜索
    3. 展示查询结果
    """
    print("\n🔍 查询向量存储")
    print("=" * 80)

    # 步骤1: 初始化 Embedding 模型（需要用相同的模型进行查询）
    print("\n步骤1: 初始化 Embedding 模型")
    print("-" * 60)
    embeddings = CustomMultimodalEmbeddings(
        api_base=EmbeddingConfig.API_BASE,
        api_key=EmbeddingConfig.API_KEY,
        model=EmbeddingConfig.MODEL
    )

    # 步骤2: 连接到已存在的 Milvus 集合
    print("\n步骤2: 连接到 Milvus 向量存储")
    print("-" * 60)

    try:
        connection_args = MilvusConfig.get_connection_args()

        # 连接到已存在的集合
        vectorstore = Milvus(
            embedding_function=embeddings,
            collection_name=MilvusConfig.COLLECTION_NAME,
            connection_args={
                **connection_args,
                "db_name": MilvusConfig.DB_NAME,
            }
        )

        print(f"✅ 成功连接到集合 '{MilvusConfig.COLLECTION_NAME}'")

        # 步骤3: 执行相似度搜索
        print("\n步骤3: 执行相似度搜索")
        print("-" * 60)

        # 定义一些查询问题
        queries = [
            "什么是机器学习？",
            "介绍一下向量数据库",
            "Python语言的特点"
        ]

        for i, query in enumerate(queries, 1):
            print(f"\n🔎 查询 {i}: {query}")
            print("-" * 40)

            # 相似度搜索，返回最相关的 top_k 个文档
            results = vectorstore.similarity_search(
                query=query,
                k=3  # 返回前3个最相似的文档
            )

            # 展示结果
            print(f"检索到的结果数量: {len(results)}")
            for j, doc in enumerate(results, 1):
                print(f"\n  结果 {j}:")
                print(f"  📄 内容: {doc.page_content}")
                # 如果有元数据，也可以展示
                if doc.metadata:
                    print(f"  📋 元数据: {doc.metadata}")

        # 步骤4: 带分数的相似度搜索
        print("\n步骤4: 带相似度分数的搜索")
        print("-" * 60)

        query = "深度学习和神经网络"
        print(f"🔎 查询: {query}")
        print("-" * 40)

        # 返回文档和相似度分数
        results_with_scores = vectorstore.similarity_search_with_score(
            query=query,
            k=3
        )

        print(f"检索到的结果数量: {len(results_with_scores)}")
        for j, (doc, score) in enumerate(results_with_scores, 1):
            print(f"\n  结果 {j}:")
            print(f"  📊 相似度分数: {score:.4f}")
            print(f"  📄 内容: {doc.page_content}")

        print("\n" + "=" * 80)
        print("✅ 查询完成")

        return vectorstore

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ========== 完整示例流程 ==========

def run_complete_example():
    """
    运行完整的向量存储和查询示例
    
    包括：
    1. 测试 Milvus 连接
    2. 创建向量存储并插入数据
    3. 执行相似度查询
    """
    print("=" * 80)
    print("🚀 RAG 向量存储与查询完整示例")
    print("=" * 80)

    # 1. 测试连接
    if not test_milvus_connection():
        print("\n❌ Milvus 连接失败，无法继续")
        return

    # 2. 创建向量存储
    vectorstore = create_vector_store()
    if not vectorstore:
        print("\n❌ 向量存储创建失败，无法继续")
        return

    # 3. 查询向量存储
    query_vector_store()

    print("\n" + "=" * 80)
    print("✅ 完整示例运行结束")
    print("=" * 80)


def main():
    """主函数：运行完整示例"""
    run_complete_example()


if __name__ == "__main__":
    main()
