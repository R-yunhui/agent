import os
import json
from dotenv import load_dotenv
from datetime import datetime

from deepagents import create_deep_agent
from typing import Literal
from tavily import TavilyClient
from langchain.messages import HumanMessage
from langchain_community.tools import tool
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.runnables import RunnableConfig

from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

caht_model = ChatTongyi(
    model=os.getenv("TONGYI_MODEL"),
    api_key=os.getenv("DASHSCOPE_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
)

# 联网搜索
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# 暂时使用内存级别的存储即可
checkpointer = InMemorySaver()


@tool
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    res = tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
    print(f"web search result: {json.dumps(res, ensure_ascii=False, indent=4)}")
    return res


def chat_with_deep_agent(query: str, session_id: str):

    system_prompt = """
    您是一位资深研究员。您的任务是进行深入研究，并撰写一份高质量的报告。 您可以使用互联网搜索工具作为收集信息的主要手段。 
    ## `internet_search` 使用此工具针对特定查询运行互联网搜索。您可以指定要返回的最大结果数、主题以及是否包含原始内容。
    ## 要求: 返回中文信息，不要返回原始内容。
    """

    deep_agent = create_deep_agent(
        model=caht_model,
        system_prompt=system_prompt,
        tools=[internet_search],
        checkpointer=checkpointer,
        debug=True,
    )

    user_query = f"""
        当前时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}
        用户问题: {query}
    """

    response = deep_agent.invoke(
        input={"message": [HumanMessage(content=user_query)]},
        config=RunnableConfig(configurable={"thread_id": session_id}),
    )

    return response["messages"][-1].content


if __name__ == "__main__":
    query = input("请输入您的问题: ")
    session_id = input("请输入会话ID: ")
    while query not in ("exit", "quit"):
        response = chat_with_deep_agent(query, session_id)
        print(f"assistant: {response}")
        query = input("请输入您的问题: ")
    print("再见！")
