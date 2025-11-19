"""
mem 模块 - 集成 mem0 和 langchain 的记忆管理

主要功能：
- Mem0LangchainChat: 集成 mem0 和 langchain 的聊天类
  每次大模型调用时自动从 mem0 获取相关记忆并加入到对话历史中
"""

from mem.mem0_langchain_chat import Mem0LangchainChat

__all__ = ["Mem0LangchainChat"]
