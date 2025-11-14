from fastmcp import FastMCP

mcp = FastMCP(
    version="1.0.0",
    name="simple_fastmcp_server",
)


@mcp.tool()
def add(a: int, b: int) -> int:
    """
    两数相加
    :param a: 第一个数
    :param b: 第二个数
    :return: 两数相加的结果
    """
    return a + b


@mcp.tool()
def get_current_time() -> str:
    """
    获取当前时间
    :return: 当前时间的字符串表示
    """
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    # 本地服务器 stdio 模式
    mcp.run(show_banner=False)

    # 远程访问的 streamable_http 方式
    # mcp.run(transport="http", port=8000)
