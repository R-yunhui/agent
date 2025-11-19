"""
演示如何使用 Mem0LangchainChat 集成 mem0 和 langchain
"""
import os
from mem import Mem0LangchainChat

# 确保向量存储目录存在
VECTOR_STORE_SAVE_DIR = "qdrant"
os.makedirs(os.path.join(os.getcwd(), VECTOR_STORE_SAVE_DIR), exist_ok=True)


def main():
    # 创建集成聊天实例
    chat = Mem0LangchainChat(
        system_prompt="你是一个专业的助手,使用通俗易懂的语言回答用户的问题",
        memory_threshold=0.2,
        memory_limit=3,
        auto_save_memory=True,
    )
    
    user_id = "alex"
    
    print("=" * 80)
    print("🧪 测试 Mem0LangchainChat 集成")
    print("=" * 80)
    
    # 测试1: 首次对话（没有记忆）
    print("\n📝 测试1: 首次对话")
    print("-" * 60)
    question1 = "我喜欢篮球和游戏"
    print(f"用户: {question1}")
    reply1 = chat.chat(question1, user_id=user_id)
    print(f"助手: {reply1}")
    
    # 测试2: 继续对话（会检索之前的记忆）
    print("\n📝 测试2: 继续对话（检索记忆）")
    print("-" * 60)
    question2 = "我刚才说我喜欢什么？"
    print(f"用户: {question2}")
    reply2 = chat.chat(question2, user_id=user_id)
    print(f"助手: {reply2}")
    
    # 测试3: 添加更多信息
    print("\n📝 测试3: 添加更多信息")
    print("-" * 60)
    question3 = "我今年25岁，来自中国"
    print(f"用户: {question3}")
    reply3 = chat.chat(question3, user_id=user_id)
    print(f"助手: {reply3}")
    
    # 测试4: 查询个人信息（会检索相关记忆）
    print("\n📝 测试4: 查询个人信息（检索记忆）")
    print("-" * 60)
    question4 = "告诉我关于我的信息"
    print(f"用户: {question4}")
    reply4 = chat.chat(question4, user_id=user_id)
    print(f"助手: {reply4}")
    
    # 测试5: 手动搜索记忆
    print("\n📝 测试5: 手动搜索记忆")
    print("-" * 60)
    memories = chat.search_memory("我喜欢什么", user_id=user_id)
    print(f"搜索 '我喜欢什么' 的结果:")
    for i, memory in enumerate(memories["results"], start=1):
        print(f"  {i}. content: {memory['memory']}. score: {memory['score']:.3f}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
