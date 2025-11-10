"""
自定义 Multimodal Embedding 类

适配非标准 OpenAI 格式的 Embedding API
API 格式示例：
{
    "model": "multimodal-embedding-v1",
    "input": {
        "contents": [
            {"text": "文本1"},
            {"text": "文本2"}
        ]
    },
    "parameters": {}
}
"""

from langchain_core.embeddings import Embeddings
from typing import List
from config.llm_config import EmbeddingConfig
import requests
import time


def _parse_response(data: dict, expected_count: int) -> List[List[float]]:
    """
    解析 API 响应

    参数:
        data: API 响应数据
        expected_count: 期望的向量数量

    返回:
        向量列表
    """
    try:
        # 尝试不同的响应格式

        # 格式1: 标准 OpenAI 格式 {"data": [{"embedding": [...]}, ...]}
        if "data" in data:
            embeddings = [item["embedding"] for item in data["data"]]
            if len(embeddings) == expected_count:
                return embeddings

        # 格式2: 直接返回 embeddings 列表 {"embeddings": [[...], [...]]}
        if "embeddings" in data:
            embeddings = data["embeddings"]
            if len(embeddings) == expected_count:
                return embeddings

        # 格式3: 嵌套在 output 中 {"output": {"embeddings": [...]}}
        if "output" in data and "embeddings" in data["output"]:
            embeddings = data["output"]["embeddings"]
            if len(embeddings) == expected_count:
                return embeddings

        # 格式4: 单个 embedding {"embedding": [...]}
        if "embedding" in data:
            return [data["embedding"]]

        # 如果都不匹配，打印响应结构以便调试
        print(f"⚠️  无法解析响应格式，响应键: {list(data.keys())}")
        if data:
            first_key = list(data.keys())[0]
            print(f"   第一个键的值类型: {type(data[first_key])}")

        raise ValueError(f"无法解析 API 响应格式: {list(data.keys())}")

    except Exception as e:
        print(f"❌ 解析响应失败: {e}")
        print(f"   响应数据: {str(data)[:200]}")
        raise


class CustomMultimodalEmbeddings(Embeddings):
    """
    自定义 Multimodal Embedding 类
    适配特定格式的 Embedding API
    
    使用示例：
        embeddings = CustomMultimodalEmbeddings(
            api_base="http://192.168.2.54:9015/v1",
            api_key="your-key",
            model="multimodal-embedding-v1"
        )
        
        # 向量化单个文本
        vector = embeddings.embed_query("这是一段文本")
        
        # 向量化多个文本
        vectors = embeddings.embed_documents(["文本1", "文本2", "文本3"])
    """

    def __init__(
            self,
            api_base: str,
            api_key: str = None,
            model: str = "multimodal-embedding-v1",
            max_retries: int = 3,
            timeout: int = 60,
            batch_size: int = 10  # 每批处理的文本数量
    ):
        """
        初始化自定义 Embeddings
        
        参数:
            api_base: API 基础 URL
            api_key: API 密钥（可选）
            model: 模型名称
            max_retries: 最大重试次数
            timeout: 请求超时时间（秒）
            batch_size: 批量处理大小
        """
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.batch_size = batch_size

        print(f"📊 初始化自定义 Embedding:")
        print(f"   API Base: {self.api_base}")
        print(f"   Model: {self.model}")
        print(f"   Batch Size: {self.batch_size}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        向量化多个文档
        
        参数:
            texts: 文本列表
            
        返回:
            向量列表
        """
        all_embeddings = []

        # 分批处理，避免单次请求过大
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        向量化单个查询
        
        参数:
            text: 查询文本
            
        返回:
            向量
        """
        embeddings = self._embed_batch([text])
        return embeddings[0]

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化文本，带重试机制
        
        参数:
            texts: 文本列表
            
        返回:
            向量列表
        """
        for attempt in range(self.max_retries):
            try:
                # 构建符合 API 格式的请求体
                contents = [{"text": text} for text in texts]

                payload = {
                    "model": self.model,
                    "input": contents,
                    "parameters": {}
                }

                # 构建请求头
                headers = {
                    "Content-Type": "application/json"
                }
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                # 发送请求
                response = requests.post(
                    f"{self.api_base}/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                # 检查响应
                if response.status_code == 200:
                    data = response.json()
                    embeddings = _parse_response(data, len(texts))
                    return embeddings
                else:
                    error_msg = f"API 返回错误 {response.status_code}: {response.text[:200]}"
                    if attempt < self.max_retries - 1:
                        print(f"⚠️  {error_msg}")
                        print(f"   重试 ({attempt + 1}/{self.max_retries})...")
                        time.sleep(1)
                    else:
                        raise Exception(error_msg)

            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️  请求失败: {e}")
                    print(f"   重试 ({attempt + 1}/{self.max_retries})...")
                    time.sleep(1)
                else:
                    print(f"❌ Embedding 最终失败: {e}")
                    # 返回零向量作为后备方案
                    print(f"⚠️  返回零向量作为后备")
                    return [[0.0] * 1536 for _ in texts]

        # 不应该到达这里
        return [[0.0] * 1536 for _ in texts]


def test_custom_embeddings():
    """测试自定义 Embeddings"""
    print("=" * 80)
    print("🧪 测试自定义 Multimodal Embeddings")
    print("=" * 80)

    # 创建 embeddings 实例
    embeddings = CustomMultimodalEmbeddings(
        api_base=EmbeddingConfig.API_BASE,
        api_key=EmbeddingConfig.API_KEY,
        model=EmbeddingConfig.MODEL,
        batch_size=3  # 测试时使用较小的批量
    )

    # 测试1：单个文本
    print("\n📝 测试1：向量化单个文本")
    print("-" * 60)
    test_text = "繁忙的城市街道"
    print(f"输入: {test_text}")

    try:
        vector = embeddings.embed_query(test_text)
        print(f"✅ 成功！")
        print(f"   向量维度: {len(vector)}")
        print(f"   前10个值: {vector[:10]}")
    except Exception as e:
        print(f"❌ 失败: {e}")

    # 测试2：多个文本
    print("\n📝 测试2：向量化多个文本")
    print("-" * 60)
    test_texts = [
        "繁忙的城市街道",
        "交通街道",
        "大量车辆出行",
        "Python 编程语言",
        "机器学习算法"
    ]
    print(f"输入: {len(test_texts)} 个文本")

    try:
        vectors = embeddings.embed_documents(test_texts)
        print(f"✅ 成功！")
        print(f"   向量数量: {len(vectors)}")
        print(f"   每个向量维度: {len(vectors[0])}")
        print(f"   第一个向量前10个值: {vectors[0][:10]}")
    except Exception as e:
        print(f"❌ 失败: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 运行测试
    test_custom_embeddings()
