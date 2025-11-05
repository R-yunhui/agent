from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory, RunnableConfig
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from dotenv import load_dotenv  # 用于加载环境变量
from typing import Dict
import os
import requests

# ============================================================================
# 第一步：加载环境变量（读取.env文件中的API密钥）
# ============================================================================
load_dotenv()  # 这会自动读取当前目录下的.env文件

llm = ChatOpenAI(
    base_url=os.getenv("OPENAI_API_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_CHAT_MODEL"),
)


def chat(user_question: str) -> str:
    """
    与OpenAI模型进行一次对话，返回模型的回复。

    :param user_question: 用户的问题或指令
    :return: 模型的回复内容
    """
    llm_response = llm.invoke(user_question)
    return llm_response.content


def chat_with_template(user_question: str) -> str:
    """
    与OpenAI模型进行一次对话，返回模型的回复。

    :param user_question: 用户的问题或指令
    :return: 模型的回复内容
    """
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的助手,使用通俗易懂的语言回答用户的问题"),
        ("human", "{user_question}"),
    ])

    # 创建一个链，将提示模板和模型连接起来
    chain = prompt_template | llm

    llm_res = chain.invoke({"user_question": user_question})
    return llm_res.content


def chat_with_memory(user_question: str) -> str:
    """
    与OpenAI模型进行一次对话，返回模型的回复。
    该函数会记住之前的对话历史，用于上下文理解。

    :param user_question: 用户的问题或指令
    :return: 模型的回复内容
    """
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的助手,使用通俗易懂的语言回答用户的问题"),
        # 对话历史
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_question}"),
    ])

    message_history = RunnableWithMessageHistory(
        prompt_template | llm,
        get_session_history=get_memory_history,
        input_messages_key="user_question",
        history_messages_key="history",
    )

    res = message_history.invoke({"user_question": user_question}, config=RunnableConfig(
        configurable={"session_id": "001"}
    ))
    return res.content


def simple_agent_chat(user_question: str) -> str:
    """
    与OpenAI模型进行一次对话，返回模型的回复。

    :param user_question: 用户的问题或指令
    :return: 模型的回复内容
    """
    system_prompt = """
    你是一个专业的助手,使用通俗易懂的语言回答用户的问题。
    """
    tools = [get_current_time]

    simple_agent = create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        debug=True  # 开启调试模式，会打印出模型的推理过程
    )

    res = simple_agent.invoke(
        input={"messages": [{"role": "user", "content": user_question}]},
    )

    return res["messages"][-1].content


@tool(description="获取当前时间的函数")
def get_current_time() -> str:
    """
    获取当前时间的函数

    :return: 当前时间的字符串表示，格式为"YYYY-MM-DD HH:MM:SS"
    """
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


chat_memory_history: Dict[str, ChatMessageHistory] = {}


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


if __name__ == "__main__":
    question = input("start：")
    while question not in ["exit", "quit", "q"]:
        response = chat_with_memory(question)
        print(response)
        question = input("start：")
    print("over")
