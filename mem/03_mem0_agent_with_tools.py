"""
完整的 mem0 + langchain agent + 工具调用示例

展示：
1. 如何将 mem0 的长期记忆集成到 agent 中
2. 工具调用的完整流程
3. 对话历史 vs 长期记忆的区别
4. 多轮对话的效果
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from mem0 import Memory
from mem0.configs.base import MemoryConfig, EmbedderConfig, VectorStoreConfig
from mem0.llms.configs import LlmConfig

from basic.embedding.custom_embeddings import CustomMultimodalEmbeddings

# 加载环境变量
load_dotenv()

VECTOR_STORE_SAVE_DIR = "qdrant"


# ============================================================================
# Mock 工具定义
# ============================================================================

@tool(description="获取当前时间")
def get_current_time() -> str:
    """获取当前时间"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


@tool(description="查询指定城市的天气信息")
def get_weather(city: str) -> str:
    """
    查询指定城市的天气
    
    Args:
        city: 城市名称，例如：北京、上海、深圳
    """
    # Mock 天气数据
    weather_data = {
        "北京": "晴天，温度 25°C，湿度 60%，适合户外活动",
        "上海": "多云，温度 22°C，湿度 70%，微风",
        "深圳": "晴天，温度 28°C，湿度 65%，适合运动",
        "广州": "小雨，温度 20°C，湿度 80%，建议带伞",
    }
    return weather_data.get(city, f"{city}今天天气晴朗，温度适中")


@tool(description="查询用户的日程安排")
def get_schedule(date: str = None) -> str:
    """
    查询用户的日程安排
    
    Args:
        date: 日期，格式：YYYY-MM-DD，如果不提供则查询今天的日程
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Mock 日程数据
    schedules = {
        datetime.now().strftime("%Y-%m-%d"): "今天：上午10点开会，下午2点打球，晚上7点看电影",
        "2024-12-26": "明天：上午9点健身，下午3点购物，晚上6点聚餐",
    }
    return schedules.get(date, f"{date}暂无安排")


@tool(description="设置提醒事项")
def set_reminder(reminder_text: str, time: str) -> str:
    """
    设置提醒事项
    
    Args:
        reminder_text: 提醒内容
        time: 提醒时间，例如：明天下午3点、2024-12-26 15:00
    """
    # Mock 设置提醒
    return f"已设置提醒：{reminder_text}，时间：{time}"


# ============================================================================
# 记忆格式化函数
# ============================================================================

def _format_memories_as_context(memories: List[Dict]) -> str:
    """
    将记忆格式化为上下文文本
    
    参数:
        memories: 记忆列表（从 mem0.search 返回的结果）
        
    返回:
        格式化的上下文文本
    """
    if not memories:
        return ""
    
    # mem0.search 返回格式：{"results": [{"memory": "...", "score": 0.8}, ...]}
    if isinstance(memories, dict) and "results" in memories:
        memory_list = memories["results"]
    elif isinstance(memories, list):
        memory_list = memories
    else:
        return ""
    
    if not memory_list:
        return ""
    
    context_parts = ["[用户相关记忆]"]
    for i, memory in enumerate(memory_list, 1):
        if isinstance(memory, dict):
            content = memory.get("memory", memory.get("content", str(memory)))
            score = memory.get("score", memory.get("similarity", ""))
            if score:
                context_parts.append(f"  {i}. {content} (相关度: {score:.3f})")
            else:
                context_parts.append(f"  {i}. {content}")
        else:
            context_parts.append(f"  {i}. {str(memory)}")
    
    return "\n".join(context_parts)


# ============================================================================
# Mem0AgentChat 类：集成 mem0 和 langchain agent
# ============================================================================

class Mem0AgentChat:
    """
    集成 mem0 和 langchain agent 的聊天类（支持工具调用）
    
    核心设计：
    1. 每次调用时从 mem0 检索相关长期记忆
    2. 将记忆注入到 SystemMessage 中（作为背景信息）
    3. 对话历史由 LangGraph 的 checkpointer 管理（短期记忆）
    4. 自动保存对话到 mem0（长期记忆）
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        embedding: Optional[CustomMultimodalEmbeddings] = None,
        tools: List = None,
        vector_store_dir: str = None,
        system_prompt: str = "你是一个智能助手，可以使用工具来回答用户的问题。",
        memory_threshold: float = 0.2,
        memory_limit: int = 5,
        auto_save_memory: bool = True,
        debug: bool = False,
    ):
        """
        初始化 Mem0AgentChat
        
        参数:
            llm: langchain 的 ChatOpenAI 实例
            embedding: 自定义 Embedding 实例
            tools: 工具列表
            vector_store_dir: 向量存储目录
            system_prompt: 基础系统提示词（记忆会动态注入）
            memory_threshold: 记忆检索的相似度阈值
            memory_limit: 最多检索的记忆数量
            auto_save_memory: 是否自动保存对话到 mem0
            debug: 是否开启调试模式
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
                        "embedding_model_dims": 3584,
                        "collection_name": "mem0",
                        "path": self.vector_store_dir
                    }
                )
            )
        )
        
        # 配置参数
        self.base_system_prompt = system_prompt
        self.memory_threshold = memory_threshold
        self.memory_limit = memory_limit
        self.auto_save_memory = auto_save_memory
        self.debug = debug
        self.tools = tools or []
        
        # 初始化 checkpointer（用于管理对话历史）
        self.checkpointer = InMemorySaver()
        
        # agent 实例（每次调用时动态创建，因为系统提示需要包含记忆）
        self._agent_cache = None
    
    def _get_relevant_memories(self, query: str, user_id: str) -> dict:
        """
        从 mem0 检索相关记忆
        
        参数:
            query: 查询文本
            user_id: 用户 ID
            
        返回:
            记忆搜索结果（dict 格式）
        """
        try:
            memories = self.memory.search(
                query=query,
                user_id=user_id,
                threshold=self.memory_threshold,
                limit=self.memory_limit
            )
            return memories if memories else {"results": []}
        except Exception as e:
            print(f"⚠️  检索记忆时出错: {e}")
            return {"results": []}
    
    def _create_agent_with_memory(self, memories: dict) -> any:
        """
        创建包含记忆上下文的 agent
        
        关键点：将记忆作为系统提示的一部分，但明确区分这是背景信息
        """
        # 构建增强的系统提示
        if memories and memories.get("results"):
            memory_context = _format_memories_as_context(memories)
            # 关键：使用清晰的结构，告诉模型这些是背景信息，不是用户当前的问题
            system_prompt = f"""{self.base_system_prompt}

{memory_context}

重要提示：上述记忆信息仅作为背景参考，帮助你了解用户的偏好和历史信息。
不要将这些记忆误解为用户的当前问题或工具调用的参数。
"""
        else:
            system_prompt = self.base_system_prompt
        
        # 创建 agent
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
            checkpointer=self.checkpointer,
            debug=self.debug,
        )
        
        return agent
    
    def chat(
        self,
        user_question: str,
        user_id: str,
        thread_id: Optional[str] = None,
        include_memories: bool = True,
    ) -> Dict:
        """
        与 agent 进行对话，自动检索并注入相关记忆
        
        参数:
            user_question: 用户问题
            user_id: 用户 ID（用于 mem0 记忆检索）
            thread_id: 线程 ID（用于对话历史管理），如果为 None 则使用 user_id
            include_memories: 是否包含记忆
            
        返回:
            包含回复和调试信息的字典
        """
        if thread_id is None:
            thread_id = user_id
        
        # 1. 从 mem0 检索相关记忆（长期记忆）
        memories = self._get_relevant_memories(user_question, user_id) if include_memories else {"results": []}
        
        if self.debug and memories.get("results"):
            print(f"\n🧠 检索到 {len(memories['results'])} 条相关记忆:")
            for mem in memories["results"]:
                print(f"  • {mem.get('memory', mem)} (相关度: {mem.get('score', 0):.3f})")
        
        # 2. 创建包含记忆的 agent
        agent = self._create_agent_with_memory(memories)
        
        # 3. 调用 agent（对话历史由 checkpointer 自动管理）
        response = agent.invoke(
            input={"messages": [{"role": "user", "content": user_question}]},
            config=RunnableConfig(
                configurable={"thread_id": thread_id}
            )
        )
        
        # 4. 提取最终回复
        assistant_reply = response["messages"][-1].content
        
        # 5. 自动保存对话到 mem0（只保存原始对话，不包含工具调用细节）
        if self.auto_save_memory:
            try:
                messages = [
                    {"role": "user", "content": user_question},
                    {"role": "assistant", "content": assistant_reply}
                ]
                self.memory.add(messages, user_id=user_id)
            except Exception as e:
                print(f"⚠️  保存记忆时出错: {e}")
        
        return {
            "reply": assistant_reply,
            "messages": response["messages"],
            "memories_used": memories.get("results", []),
        }
    
    def add_memory(self, messages: List[Dict], user_id: str):
        """手动添加记忆到 mem0"""
        self.memory.add(messages, user_id=user_id)
    
    def search_memory(self, query: str, user_id: str, threshold: Optional[float] = None, limit: Optional[int] = None) -> dict:
        """搜索记忆"""
        return self.memory.search(
            query=query,
            user_id=user_id,
            threshold=threshold or self.memory_threshold,
            limit=limit or self.memory_limit
        )


# ============================================================================
# 示例演示
# ============================================================================

def print_separator(title: str = ""):
    """打印分隔线"""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print('=' * 80)
    else:
        print('-' * 80)


def print_message_flow(messages: List, title: str = "消息流"):
    """打印消息流（用于调试）"""
    print(f"\n📋 {title}:")
    for i, msg in enumerate(messages, 1):
        role = msg.get("role", type(msg).__name__)
        content = msg.get("content", str(msg))[:100]  # 只显示前100字符
        print(f"  {i}. [{role}] {content}...")


def main():
    """主函数：演示完整的使用流程"""
    
    # 确保向量存储目录存在
    os.makedirs(os.path.join(os.getcwd(), VECTOR_STORE_SAVE_DIR), exist_ok=True)
    
    # 创建聊天实例
    chat = Mem0AgentChat(
        tools=[get_current_time, get_weather, get_schedule, set_reminder],
        system_prompt="你是一个智能助手，可以帮助用户查询天气、时间、日程，并设置提醒。",
        memory_threshold=0.2,
        memory_limit=5,
        auto_save_memory=True,
        debug=True,  # 开启调试模式，可以看到记忆检索和工具调用过程
    )
    
    user_id = "demo_user"
    thread_id = "demo_thread"
    
    print_separator("🚀 Mem0 + LangChain Agent + 工具调用完整示例")
    
    # ========================================================================
    # 场景1: 首次对话 - 用户提供个人信息（会保存到 mem0）
    # ========================================================================
    print_separator("场景1: 首次对话 - 用户提供个人信息")
    
    question1 = "我叫张三，住在北京，喜欢打篮球，每天早上7点起床"
    print(f"👤 用户: {question1}")
    
    result1 = chat.chat(question1, user_id=user_id, thread_id=thread_id)
    print(f"🤖 助手: {result1['reply']}")
    
    print(f"\n💾 已保存到 mem0 的长期记忆")
    print(f"📝 对话历史已保存到 checkpointer (thread_id: {thread_id})")
    
    # ========================================================================
    # 场景2: 查询天气 - 应该利用记忆中的城市信息
    # ========================================================================
    print_separator("场景2: 查询天气 - 利用长期记忆")
    
    question2 = "今天天气怎么样？"
    print(f"👤 用户: {question2}")
    print("💡 提示: 助手应该从 mem0 检索到用户住在北京，然后调用 get_weather('北京')")
    
    result2 = chat.chat(question2, user_id=user_id, thread_id=thread_id)
    print(f"🤖 助手: {result2['reply']}")
    
    if result2['memories_used']:
        print(f"\n🧠 使用的记忆:")
        for mem in result2['memories_used']:
            print(f"  • {mem.get('memory', '')}")
    
    # ========================================================================
    # 场景3: 查询时间 - 工具调用，不受记忆影响
    # ========================================================================
    print_separator("场景3: 查询时间 - 工具调用")
    
    question3 = "现在几点了？"
    print(f"👤 用户: {question3}")
    print("💡 提示: 应该调用 get_current_time() 工具")
    
    result3 = chat.chat(question3, user_id=user_id, thread_id=thread_id)
    print(f"🤖 助手: {result3['reply']}")
    
    # ========================================================================
    # 场景4: 查询日程 - 利用记忆中的起床时间
    # ========================================================================
    print_separator("场景4: 查询日程 - 利用长期记忆")
    
    question4 = "我今天的日程安排是什么？"
    print(f"👤 用户: {question4}")
    print("💡 提示: 应该调用 get_schedule() 工具")
    
    result4 = chat.chat(question4, user_id=user_id, thread_id=thread_id)
    print(f"🤖 助手: {result4['reply']}")
    
    # ========================================================================
    # 场景5: 设置提醒 - 利用记忆中的偏好
    # ========================================================================
    print_separator("场景5: 设置提醒 - 利用长期记忆")
    
    question5 = "提醒我明天早上打球"
    print(f"👤 用户: {question5}")
    print("💡 提示: 助手知道用户喜欢打篮球（来自记忆），应该调用 set_reminder()")
    
    result5 = chat.chat(question5, user_id=user_id, thread_id=thread_id)
    print(f"🤖 助手: {result5['reply']}")
    
    # ========================================================================
    # 场景6: 新会话 - 展示跨会话记忆
    # ========================================================================
    print_separator("场景6: 新会话 - 跨会话记忆")
    
    new_thread_id = "new_thread"
    question6 = "我喜欢什么运动？"
    print(f"👤 用户: {question6}")
    print(f"💡 提示: 这是新会话 (thread_id: {new_thread_id})，但会从 mem0 检索到用户喜欢打篮球")
    
    result6 = chat.chat(question6, user_id=user_id, thread_id=new_thread_id)
    print(f"🤖 助手: {result6['reply']}")
    
    if result6['memories_used']:
        print(f"\n🧠 使用的记忆（跨会话检索）:")
        for mem in result6['memories_used']:
            print(f"  • {mem.get('memory', '')} (相关度: {mem.get('score', 0):.3f})")
    
    # ========================================================================
    # 场景7: 手动搜索记忆
    # ========================================================================
    print_separator("场景7: 手动搜索记忆")
    
    search_query = "用户住在哪里"
    memories = chat.search_memory(search_query, user_id=user_id)
    print(f"🔍 搜索查询: '{search_query}'")
    print(f"📊 找到 {len(memories.get('results', []))} 条相关记忆:")
    for i, mem in enumerate(memories.get('results', []), 1):
        print(f"  {i}. {mem.get('memory', '')} (相关度: {mem.get('score', 0):.3f})")
    
    print_separator("✅ 示例演示完成")
    
    print("\n📚 总结:")
    print("  1. 长期记忆（mem0）: 跨会话保存用户画像和偏好")
    print("  2. 短期记忆（checkpointer）: 管理当前会话的对话历史")
    print("  3. 工具调用: 不受记忆影响，正常提取参数和执行")
    print("  4. 记忆注入: 作为 SystemMessage 的一部分，作为背景信息")


if __name__ == "__main__":
    main()
