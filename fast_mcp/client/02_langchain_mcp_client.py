"""
使用 langchain mcp client 调用 mcp server
"""
import json
import os
import asyncio

from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_core.runnables import RunnableConfig
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver

from typing import Dict

# 加载配置
load_dotenv()

# 大模型 ChatModel
llm = ChatTongyi(
    api_key=os.getenv("DASHSCOPE_KEY"),
    model=os.getenv("TONGYI_CHAT_MODEL"),
)

"""
配置 MCP 客户端
Must be one of: 'stdio', 'sse', 'websocket', 'streamable_http'
"""
client = MultiServerMCPClient(
    {
        # "simple_fastmcp_server": {
        #     "transport": "streamable_http",
        #     "url": "http://127.0.0.1:8000/mcp",
        # },
        "local_mcp_server": {
            "transport": "stdio",
            "args": [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server",
                                  "01_simple_fastmcp_server.py")],
            "command": "python"
        },
        "12306-mcp": {
            "command": "C:\\Program Files\\nodejs\\npx.cmd",
            "args": [
                "-y",
                "12306-mcp"
            ],
            "transport": "stdio",
        }
    },
)

tools: list[BaseTool] = []

agent = None
checkpointer = None


async def main(user_question: str, thread_id: str):
    try:
        response = await agent.ainvoke(
            input={"messages": [{"role": "user", "content": user_question}]},
            config=RunnableConfig(
                configurable={"thread_id": thread_id}
            )
        )

        print(f"大模型完整消息: {response}")

        print(f"大模型回复: {response['messages'][-1].content}")
    except Exception as e:
        print(f"大模型调用失败: {e}")


def get_or_create_agent():
    """
    获取或创建一个智能助手
    :return: 智能助手
    """
    global agent, checkpointer
    if not agent:
        checkpointer = InMemorySaver()

        agent = create_agent(
            llm,
            tools,
            system_prompt="你是一个智能助手, 你可以使用以下工具来回答用户的问题。",
            checkpointer=checkpointer,
            debug=True,
        )

    return agent


async def get_mcp_tools():
    mcp_tools = await client.get_tools()
    if mcp_tools:
        print(
            f"成功获取 MCP 工具: {len(mcp_tools)} 个, 工具名称: {[tool.name for tool in mcp_tools]}, 加入到 tools 中, 共 {len(tools)} 个")

        for tool in mcp_tools:
            print(f"工具名称: {tool.name}, 工具描述: {tool.description}, 工具参数: {tool.args}")

        tools.extend(mcp_tools)


def get_history(thread_id: str):
    """
    获取指定线程的对话历史
    :param thread_id: 线程 ID
    :return: 对话历史
    """
    global checkpointer
    if checkpointer:
        message_list = []
        checkpoint = checkpointer.get_tuple(config=RunnableConfig(configurable={"thread_id": thread_id}))
        messages = checkpoint.checkpoint['channel_values']['messages']
        for msg in messages:
            print(msg.type, msg.content, end="\n")
            message_list.append(msg)

    return None


if __name__ == "__main__":
    asyncio.run(get_mcp_tools())
    print(f"成功获取工具: {len(tools)} 个")
    print("=" * 60)
    # 获取或创建智能助手
    get_or_create_agent()
    print("成功创建智能助手")
    print("=" * 60)
    chat_id = "001"
    question = input("请输入问题. 输入 exit 或 退出 结束: ")
    while question not in ["exit", "退出"]:
        if question == '获取对话历史':
            get_history(chat_id)
        else:
            asyncio.run(main(question, chat_id))
        question = input("请输入问题: ")

    print("程序结束")
