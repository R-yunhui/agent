"""
学习 aiohttp 库
"""
import aiohttp
import asyncio


async def main():
    async with aiohttp.ClientSession() as session:
        # GET请求
        async with session.get("https://httpbin.org/get") as resp:
            print(resp.status)  # 状态码
            print(resp.headers)  # 响应头
            text = await resp.text()  # 文本内容
            json_data = await resp.json()  # JSON解析
            binary = await resp.read()  # 二进制内容
            print(f"文本内容: {text}")
            print(f"JSON数据: {json_data}")
            print(f"二进制内容: {binary}")


asyncio.run(main())
