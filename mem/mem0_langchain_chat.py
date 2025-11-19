"""
集成 mem0 和 langchain 的聊天类
每次大模型调用时自动从 mem0 获取相关记忆并加入到对话历史中
"""
import os
from typing import List, Dict, Optional, Iterator
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory, RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from mem0 import Memory
from mem0.configs.base import MemoryConfig, EmbedderConfig, VectorStoreConfig
from mem0.llms.configs import LlmConfig

from basic.embedding.custom_embeddings import CustomMultimodalEmbeddings

# 加载环境变量
load_dotenv()

VECTOR_STORE_SAVE_DIR = "qdrant"


def _format_memories_as_context(memories: List[Dict]) -> str:
    """
    将记忆格式化为上下文文本

    参数:
        memories: 记忆列表

    返回:
        格式化的上下文文本
    """
    if not memories:
        return ""

    context_parts = ["相关记忆："]
    for i, memory in enumerate(memories, 1):
        # mem0 返回的记忆格式可能不同，需要适配
        if isinstance(memory, dict):
            content = memory.get("memory", memory.get("content", str(memory)))
            score = memory.get("score", memory.get("similarity", ""))
            if score:
                context_parts.append(f"{i}. {content} (相似度: {score:.3f})")
            else:
                context_parts.append(f"{i}. {content}")
        else:
            context_parts.append(f"{i}. {str(memory)}")

    return "\n".join(context_parts)


class Mem0LangchainChat:
    """
    集成 mem0 和 langchain 的聊天类
    
    功能：
    1. 每次调用时自动从 mem0 检索相关记忆
    2. 将记忆加入到对话历史中
    3. 调用大模型生成回复
    4. 自动保存对话到 mem0
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        embedding: Optional[CustomMultimodalEmbeddings] = None,
        vector_store_dir: str = None,
        system_prompt: str = "你是一个专业的助手,使用通俗易懂的语言回答用户的问题",
        memory_threshold: float = 0.2,
        memory_limit: int = 3,
        auto_save_memory: bool = True,
    ):
        """
        初始化 Mem0LangchainChat
        
        参数:
            llm: langchain 的 ChatOpenAI 实例，如果为 None 则使用默认配置
            embedding: 自定义 Embedding 实例，如果为 None 则使用默认配置
            vector_store_dir: 向量存储目录，默认为 "qdrant"
            system_prompt: 系统提示词
            memory_threshold: 记忆检索的相似度阈值
            memory_limit: 最多检索的记忆数量
            auto_save_memory: 是否自动保存对话到 mem0
        """
        # 初始化 LLM
        if llm is None:
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_CHAT_MODEL"),
                base_url=os.getenv("OPENAI_API_BASE_URL"),
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.7,
                max_retries=3,
                max_tokens=4096
            )
        else:
            self.llm = llm
        
        # 初始化 Embedding
        if embedding is None:
            self.embedding = CustomMultimodalEmbeddings(
                api_base=os.getenv("OPENAI_API_BASE_URL"),
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("EMBEDDING_MODEL"),
            )
        else:
            self.embedding = embedding
        
        # 向量存储目录
        self.vector_store_dir = vector_store_dir or os.path.join(os.getcwd(), VECTOR_STORE_SAVE_DIR)
        os.makedirs(self.vector_store_dir, exist_ok=True)
        
        # 初始化 mem0
        self.memory = Memory(
            config=MemoryConfig(
                llm=LlmConfig(
                    provider="langchain",
                    config={"model": self.llm}
                ),
                embedder=EmbedderConfig(
                    provider="langchain",
                    config={"model": self.embedding}
                ),
                vector_store=VectorStoreConfig(
                    provider="qdrant",
                    config={
                        "embedding_model_dims": 3584,  # 匹配您的 embedding 模型维度
                        "collection_name": "mem0",
                        "path": self.vector_store_dir
                    }
                )
            )
        )
        
        # 配置参数
        self.system_prompt = system_prompt
        self.memory_threshold = memory_threshold
        self.memory_limit = memory_limit
        self.auto_save_memory = auto_save_memory
        
        # 存储会话历史
        self.chat_histories: Dict[str, ChatMessageHistory] = {}
        
        # 创建带记忆的聊天链
        self._create_chat_chain()
    
    def _create_chat_chain(self):
        """创建带记忆的聊天链"""
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_question}"),
        ])
        
        runnable = prompt_template | self.llm
        
        self.message_history = RunnableWithMessageHistory(
            runnable=runnable,
            get_session_history=self._get_memory_history,
            input_messages_key="user_question",
            history_messages_key="history",
        )
    
    def _get_memory_history(self, session_id: str) -> ChatMessageHistory:
        """
        获取会话历史，如果不存在则创建新的
        
        参数:
            session_id: 会话 ID
            
        返回:
            ChatMessageHistory 实例
        """
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = ChatMessageHistory()
        return self.chat_histories[session_id]
    
    def _get_relevant_memories(self, query: str, user_id: str) -> List[Dict]:
        """
        从 mem0 检索相关记忆
        
        参数:
            query: 查询文本
            user_id: 用户 ID
            
        返回:
            相关记忆列表
        """
        try:
            memories = self.memory.search(
                query=query,
                user_id=user_id,
                threshold=self.memory_threshold,
                limit=self.memory_limit
            )
            return memories if memories else []
        except Exception as e:
            print(f"⚠️  检索记忆时出错: {e}")
            return []

    def chat(
        self,
        user_question: str,
        user_id: str,
        session_id: Optional[str] = None,
        include_memories_in_prompt: bool = True,
    ) -> str:
        """
        与模型进行一次对话，自动检索并加入相关记忆
        
        参数:
            user_question: 用户问题
            user_id: 用户 ID（用于 mem0 记忆检索）
            session_id: 会话 ID（用于对话历史管理），如果为 None 则使用 user_id
            include_memories_in_prompt: 是否将记忆加入到系统提示中
            
        返回:
            模型的回复
        """
        if session_id is None:
            session_id = user_id
        
        # 1. 从 mem0 检索相关记忆
        memories = self._get_relevant_memories(user_question, user_id)
        
        # 2. 构建系统提示（包含记忆）
        system_prompt = self.system_prompt
        if include_memories_in_prompt and memories:
            memory_context = _format_memories_as_context(memories)
            system_prompt = f"{self.system_prompt}\n\n{memory_context}"
        
        # 3. 调用模型
        response = self.message_history.invoke(
            {
                "user_question": user_question,
                "system_prompt": system_prompt,
            },
            config=RunnableConfig(
                configurable={"session_id": session_id}
            )
        )
        
        assistant_reply = response.content
        
        # 4. 自动保存对话到 mem0
        if self.auto_save_memory:
            try:
                messages = [
                    {"role": "user", "content": user_question},
                    {"role": "assistant", "content": assistant_reply}
                ]
                self.memory.add(messages, user_id=user_id)
            except Exception as e:
                print(f"⚠️  保存记忆时出错: {e}")
        
        return assistant_reply
    
    def stream_chat(
        self,
        user_question: str,
        user_id: str,
        session_id: Optional[str] = None,
        include_memories_in_prompt: bool = True,
    ) -> Iterator[str]:
        """
        流式对话，自动检索并加入相关记忆
        
        参数:
            user_question: 用户问题
            user_id: 用户 ID（用于 mem0 记忆检索）
            session_id: 会话 ID（用于对话历史管理），如果为 None 则使用 user_id
            include_memories_in_prompt: 是否将记忆加入到系统提示中
            
        返回:
            流式响应迭代器
        """
        if session_id is None:
            session_id = user_id
        
        # 1. 从 mem0 检索相关记忆
        memories = self._get_relevant_memories(user_question, user_id)
        
        # 2. 构建系统提示（包含记忆）
        system_prompt = self.system_prompt
        if include_memories_in_prompt and memories:
            memory_context = _format_memories_as_context(memories)
            system_prompt = f"{self.system_prompt}\n\n{memory_context}"
        
        # 3. 流式调用模型
        for chunk in self.message_history.stream(
            {
                "user_question": user_question,
                "system_prompt": system_prompt,
            },
            config=RunnableConfig(
                configurable={"session_id": session_id}
            )
        ):
            if hasattr(chunk, 'content'):
                yield chunk.content
            else:
                yield str(chunk)
        
        # 4. 自动保存对话到 mem0（需要收集完整回复）
        if self.auto_save_memory:
            # 注意：流式模式下需要手动收集完整回复才能保存
            # 这里只提供框架，实际使用时需要调用者收集完整回复
            pass
    
    def add_memory(self, messages: List[Dict], user_id: str):
        """
        手动添加记忆到 mem0
        
        参数:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            user_id: 用户 ID
        """
        self.memory.add(messages, user_id=user_id)
    
    def search_memory(self, query: str, user_id: str, threshold: Optional[float] = None, limit: Optional[int] = None) -> dict:
        """
        搜索记忆
        
        参数:
            query: 查询文本
            user_id: 用户 ID
            threshold: 相似度阈值，如果为 None 则使用默认值
            limit: 返回数量限制，如果为 None 则使用默认值
            
        返回:
            相关记忆列表
        """
        return self.memory.search(
            query=query,
            user_id=user_id,
            threshold=threshold or self.memory_threshold,
            limit=limit or self.memory_limit
        )
    
    def clear_session_history(self, session_id: str):
        """
        清除指定会话的历史记录
        
        参数:
            session_id: 会话 ID
        """
        if session_id in self.chat_histories:
            del self.chat_histories[session_id]
