"""
联网检索 agent
"""

from langchain_community.chat_models.tongyi import ChatTongyi
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()


llm = ChatTongyi(
    model=os.getenv("TONGYI_MODEL"),
    api_key=os.getenv("DASHSCOPE_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
)


@tool
def bocha_websearch_tool(query: str, count: int = 10) -> str:
    """
    使用Bocha Web Search API 进行网页搜索。

    Args:
        query (str): 搜索关键词
        count (int, optional): 搜索结果数量. Defaults to 10.
    Returns:
        str: 搜索结果的详细信息，包括网页标题、网页URL、网页摘要、网站名称、网站Icon、网页发布时间等。
    """
    url = "https://api.bochaai.com/v1/web-search"

    headers = {
        "Authorization": f"Bearer {'sk-77103117515748ca9df587b606992aa4'}",  # 请替换为你的API密钥
        "Content-Type": "application/json",
    }

    data = {
        "query": query,
        "freshness": "noLimit",  # 搜索的时间范围，例如 "oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"
        "summary": True,  # 是否返回长文本摘要
        "count": count,
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        json_response = response.json()
        try:
            if json_response["code"] != 200 or not json_response["data"]:
                return f"搜索API请求失败，原因是: {response.msg or '未知错误'}"

            webpages = json_response["data"]["webPages"]["value"]
            if not webpages:
                return "未找到相关结果。"
            formatted_results = ""
            for idx, page in enumerate(webpages, start=1):
                formatted_results += (
                    f"引用: {idx}\n"
                    f"标题: {page['name']}\n"
                    f"URL: {page['url']}\n"
                    f"摘要: {page['summary']}\n"
                    f"网站名称: {page['siteName']}\n"
                    f"网站图标: {page['siteIcon']}\n"
                    f"发布时间: {page['dateLastCrawled']}\n\n"
                )
            return formatted_results.strip()
        except Exception as e:
            return f"搜索API请求失败，原因是：搜索结果解析失败 {str(e)}"
    else:
        return f"搜索API请求失败，状态码: {response.status_code}, 错误信息: {response.text}"


# 定义记忆存储，暂时使用内存存储
checkpointer = InMemorySaver()


def chat(question: str, session_id: str) -> str | None:
    # 定义大模型, 绑定工具
    tools = [bocha_websearch_tool]

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="你是一个专业的聊天助手,可以使用通俗易懂的语言回复用户的问题",
        debug=False,
        checkpointer=checkpointer,
    )

    human_message = f"""
    当前时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    用户问题: {question}
    """

    response = agent.invoke(
        input={"messages": [HumanMessage(content=human_message)]},
        config=RunnableConfig(configurable={"thread_id": session_id}),
    )

    return response["messages"][-1].content


def main(query: str):
    res = chat(query, "session_id")
    print(f"大模型返回结果: {res}")


if __name__ == "__main__":
    main("请帮我分析一下最近1年成都二手房的价格变化趋势,并给出一些购房建议")
