import asyncio
from fastmcp import Client

client = Client("http://localhost:8000/mcp")


async def call_tool(name: str):
    # 服务器使用 HTTP 传输运行，因此需要异步调用
    async with client:
        mcp_tools = await client.list_tools()
        if mcp_tools:
            for tool in mcp_tools:
                print(tool)
        result = await client.call_tool("add", {"a": 1, "b": 2})
        print(result)


asyncio.run(call_tool("Ford"))
