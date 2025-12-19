"""
旅行助手
"""
import os
import asyncio
import aiohttp
import faker as faker_module

from typing import TypedDict, List

from dotenv import load_dotenv

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool, BaseTool
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.types import StreamMode

# 加载 .env
load_dotenv()

# mock数据
fake = faker_module.Faker(
    locale="zh_CN",
)

# web_search 相关的信息
web_search_url = os.getenv("WEB_SEARCH_URL")
web_search_api_key = os.getenv("WEB_SEARCH_API_KEY")

# 暂时使用内存作为 memory
memory_saver = InMemorySaver()

# mcp tools 缓存
_mcp_tools_cache: dict[str, List[BaseTool]] = {}


def _get_chat_model():
    return ChatTongyi(
        api_key=os.getenv("DASHSCOPE_KEY"),
        model=os.getenv("TONGYI_MODEL"),
        max_retries=3,
        streaming=True,
    )


def _get_agent(llm: BaseChatModel, system_prompt: str):
    mcp_tools = _mcp_tools_cache.get("12306-mcp", [])
    tools = mcp_tools + [web_search_tool]
    return create_agent(
        model=llm,
        tools=tools,
        checkpointer=memory_saver,
        system_prompt=system_prompt,
        debug=True
    )


class TravelState(TypedDict):
    # 用户的原始问题
    user_question: str

    # 联网检索结果
    web_search_result: dict


async def chat(query: str, user_id: str):
    try:
        llm = _get_chat_model()
        agent = _get_agent(llm, "你是一个专业的聊天助手，可以使用各种工具来辅助回答用户的问题")

        inputs = {"messages": [HumanMessage(content=query)]}
        config = RunnableConfig(configurable={"thread_id": user_id})

        print("AI: ", end="", flush=True)

        # 使用 stream_mode="messages" 实现真正的 token 级别流式输出
        async for msg, metadata in agent.astream(inputs, config=config, stream_mode="messages"):
            # msg 是 AIMessageChunk，metadata 包含 langgraph_node 等信息
            # 只输出 AI 模型生成的内容，跳过工具调用
            if msg.content and metadata.get("langgraph_node") == "model":
                print(msg.content, end="", flush=True)

        print()  # 换行
    except Exception as e:
        print(f"\n大模型调用异常, error: {e}")


async def _get_mcp_tools(server_name: str) -> List[BaseTool]:
    """获取 MCP 工具，带缓存"""
    if server_name in _mcp_tools_cache:
        return _mcp_tools_cache[server_name]

    client = MultiServerMCPClient(
        connections={
            "12306-mcp": {
                "command": "C:\\Program Files\\nodejs\\npx.cmd",
                "args": [
                    "-y",
                    "12306-mcp"
                ],
                "transport": "stdio",
            }
        }
    )
    base_tools = await client.get_tools()
    for idx, base_tool in enumerate(base_tools):
        print(f"序号: {idx}")
        print(f"工具名称: {base_tool.name}")
        print(f"工具描述: {base_tool.description}")
        print(f"工具参数信息: {base_tool.args}")

    _mcp_tools_cache[server_name] = base_tools
    return base_tools


@tool(description="使用Bocha Web Search API 进行网页搜索。")
def web_search_tool(query: str, count: int = 10) -> str:
    """
    使用Bocha Web Search API 进行网页搜索。

    Args:
        query (str): 搜索关键词
        count (int, optional): 搜索结果数量. Defaults to 10.
    Returns:
        str: 搜索结果的详细信息，包括网页标题、网页URL、网页摘要、网站名称、网站Icon、网页发布时间等。
    """
    return asyncio.run(web_search(query, count))


async def web_search(user_question: str, count: int) -> str:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                    url=web_search_url,
                    headers={
                        "Authorization": f"Bearer {web_search_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": user_question,
                        "freshness": "oneWeek",  # 搜索的时间范围，例如 "oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"
                        "summary": True,  # 返回摘要数据
                        "count": count  # 返回 top 数据
                    }
            ) as resp:
                result = await resp.json()
                status = resp.status

                if status == 200:
                    try:
                        if result.get('code') == 200 and result.get('data'):
                            web_pages = result['data'].get('webPages', {})
                            web_pages_value = web_pages.get('value', [])

                            if not web_pages_value:
                                return "未找到相关搜索结果"

                            formatted_results = ""
                            for idx, page in enumerate(web_pages_value):
                                formatted_results += (
                                    f"引用: {idx}\n"
                                    f"标题: {page.get('name', '')}\n"
                                    f"URL: {page.get('url', '')}\n"
                                    f"摘要: {page.get('summary', '')}\n"
                                    f"网站名称: {page.get('siteName', '')}\n"
                                    f"网站图标: {page.get('siteIcon', '')}\n"
                                    f"发布时间: {page.get('dateLastCrawled', '')}\n\n"
                                )
                            return formatted_results.strip()
                        else:
                            return f"搜索返回错误: {result.get('msg', '未知错误')}"
                    except Exception as e1:
                        print(f"解析搜索结果异常: {e1}")
                        return f"解析搜索结果异常: {e1}"
                else:
                    return f"搜索请求失败，状态码: {status}"
        except Exception as e:
            print(f"联网检索异常, error: {e}")
            return f"联网检索异常: {e}"


async def main():
    await _get_mcp_tools("12306-mcp")
    print("=" * 60)
    query = input("用户问题: ")
    user_id = f"id-{fake.random_int(5, 10)}"
    while query not in ('exit', 'quit'):
        await chat(query=query.strip(), user_id=user_id)
        query = input("用户问题: ")
    else:
        print("结束大模型聊天")


if __name__ == "__main__":
    asyncio.run(main())
