from fastmcp import FastMCP

mcp = FastMCP(
    version="1.0.0",
    name="simple_fastmcp_server",
)


@mcp.tool(description="两数相加, 返回两个数的和")
def add(a: int, b: int) -> int:
    return a + b


@mcp.tool(description="获取当前时间, 格式为 %Y-%m-%d %H:%M:%S")
def get_current_time() -> str:
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    # 本地服务器 stdio 模式
    mcp.run(show_banner=False)

    # 远程访问的 streamable_http 方式
    # mcp.run(transport="http", port=8000)
