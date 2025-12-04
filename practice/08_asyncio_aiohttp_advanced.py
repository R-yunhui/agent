"""
学习 asyncio + aiohttp 高级特性
涵盖：不同HTTP方法、会话管理、超时设置、异常处理、并发控制、文件上传等
"""
import aiohttp
import asyncio
from typing import List, Dict, Any


async def http_methods_demo():
    """
    演示不同的HTTP方法：GET, POST, PUT, DELETE, PATCH
    """
    print("=" * 60)
    print("演示不同的HTTP方法")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 1. GET请求 - 查询参数
        print("\n1. GET请求 (带查询参数):")
        params = {"key1": "value1", "key2": "value2"}
        try:
            async with session.get("https://httpbin.org/get", params=params) as resp:
                result = await resp.json()
                print(f"状态码: {resp.status}")
                print(f"请求URL: {result['url']}")
                print(f"查询参数: {result['args']}")
        except Exception as e:
            print(f"GET请求失败: {type(e).__name__}: {e}")
        
        # 2. POST请求 - JSON数据
        print("\n2. POST请求 (JSON数据):")
        json_data = {"name": "test", "age": 20}
        try:
            async with session.post("https://httpbin.org/post", json=json_data) as resp:
                result = await resp.json()
                print(f"状态码: {resp.status}")
                print(f"提交的JSON: {result['json']}")
        except Exception as e:
            print(f"POST(JSON)请求失败: {type(e).__name__}: {e}")
        
        # 3. POST请求 - 表单数据
        print("\n3. POST请求 (表单数据):")
        form_data = aiohttp.FormData()
        form_data.add_field("username", "test_user")
        form_data.add_field("password", "test_pass")
        try:
            async with session.post("https://httpbin.org/post", data=form_data) as resp:
                result = await resp.json()
                print(f"状态码: {resp.status}")
                print(f"提交的表单: {result['form']}")
        except Exception as e:
            print(f"POST(表单)请求失败: {type(e).__name__}: {e}")
        
        # 4. PUT请求
        print("\n4. PUT请求:")
        put_data = {"updated": True, "value": 100}
        try:
            async with session.put("https://httpbin.org/put", json=put_data) as resp:
                result = await resp.json()
                print(f"状态码: {resp.status}")
                print(f"提交的数据: {result.get('json', 'N/A')}")
        except Exception as e:
            print(f"PUT请求失败: {type(e).__name__}: {e}")
        
        # 5. DELETE请求
        print("\n5. DELETE请求:")
        try:
            async with session.delete("https://httpbin.org/delete") as resp:
                result = await resp.json()
                print(f"状态码: {resp.status}")
                print(f"响应内容: {result}")
        except Exception as e:
            print(f"DELETE请求失败: {type(e).__name__}: {e}")
        
        # 6. PATCH请求
        print("\n6. PATCH请求:")
        patch_data = {"partial_update": "this field was updated"}
        try:
            async with session.patch("https://httpbin.org/patch", json=patch_data) as resp:
                result = await resp.json()
                print(f"状态码: {resp.status}")
                print(f"提交的数据: {result.get('json', 'N/A')}")
        except Exception as e:
            print(f"PATCH请求失败: {type(e).__name__}: {e}")
            print("继续执行其他演示...")


async def session_management_demo():
    """
    演示会话管理：自定义头、cookie、连接池等
    """
    print("\n" + "=" * 60)
    print("演示会话管理")
    print("=" * 60)
    
    # 1. 自定义默认头
    headers = {
        "User-Agent": "My-Aiohttp-Client/1.0",
        "X-Custom-Header": "custom-value"
    }
    
    # 2. 自定义连接池设置
    conn = aiohttp.TCPConnector(
        limit=10,  # 连接池最大连接数
        limit_per_host=5,  # 每个主机的最大连接数
    )
    
    # 3. 自定义超时设置
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(headers=headers, connector=conn, timeout=timeout) as session:
        # 发送请求，检查自定义头
        print("\n1. 检查自定义头:")
        async with session.get("https://httpbin.org/get") as resp:
            result = await resp.json()
            print(f"状态码: {resp.status}")
            print(f"请求头: {result['headers']}")
        
        # 2. Cookie管理
        print("\n2. Cookie管理:")
        # 先设置cookie
        async with session.get("https://httpbin.org/cookies/set?name=test&value=123") as resp:
            await resp.text()
        
        # 查看cookie
        async with session.get("https://httpbin.org/cookies") as resp:
            result = await resp.json()
            print(f"状态码: {resp.status}")
            print(f"当前Cookie: {result['cookies']}")


async def timeout_and_error_handling():
    """
    演示超时设置和异常处理
    """
    print("\n" + "=" * 60)
    print("演示超时设置和异常处理")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 1. 全局超时设置
        print("\n1. 全局超时设置 (1秒):")
        try:
            async with session.get("https://httpbin.org/delay/2", timeout=1) as resp:
                await resp.text()
        except asyncio.TimeoutError:
            print("✓ 超时异常捕获成功")
        
        # 2. 分阶段超时设置
        print("\n2. 分阶段超时设置:")
        timeout = aiohttp.ClientTimeout(
            connect=0.5,  # 连接超时
            sock_read=1.0,  # 读取超时
            total=2.0  # 总超时
        )
        
        try:
            async with session.get("https://httpbin.org/delay/2", timeout=timeout) as resp:
                await resp.text()
        except asyncio.TimeoutError:
            print("✓ 分阶段超时异常捕获成功")
        
        # 3. 其他异常处理
        print("\n3. 其他异常处理:")
        try:
            # 无效URL
            async with session.get("https://invalid-url-123456.com") as resp:
                await resp.text()
        except aiohttp.ClientError as e:
            print(f"✓ 客户端异常捕获成功: {type(e).__name__}")
        
        # 4. 状态码处理
        print("\n4. 状态码处理:")
        async with session.get("https://httpbin.org/status/404") as resp:
            if resp.status >= 400:
                print(f"✓ 错误状态码处理: {resp.status} {resp.reason}")
                # 可以选择抛出异常
                # resp.raise_for_status()


async def semaphore_concurrency_control():
    """
    演示使用信号量控制并发
    """
    print("\n" + "=" * 60)
    print("演示使用信号量控制并发")
    print("=" * 60)
    
    # 要请求的URL列表
    urls = [
        "https://httpbin.org/delay/1" for _ in range(10)
    ]
    
    # 限制最大并发数
    concurrency_limit = 3
    semaphore = asyncio.Semaphore(concurrency_limit)
    
    async def fetch_with_semaphore(url: str, idx: int) -> Dict[str, Any]:
        """使用信号量的fetch函数"""
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                try:
                    start_time = asyncio.get_event_loop().time()
                    async with session.get(url, timeout=5) as resp:
                        data = await resp.json()
                        elapsed = asyncio.get_event_loop().time() - start_time
                        print(f"任务 {idx+1:2d} | 状态: {resp.status} | 耗时: {elapsed:.2f}s")
                        return {"url": url, "status": resp.status, "elapsed": elapsed}
                except Exception as e:
                    print(f"任务 {idx+1:2d} | 错误: {type(e).__name__}")
                    return {"url": url, "status": 0, "error": str(e)}
    
    concurrency_limit = 3
    # 执行并发请求
    print(f"\n开始并发请求 {len(urls)} 个URL，最大并发数: {concurrency_limit}")
    start_time = asyncio.get_event_loop().time()
    
    tasks = [fetch_with_semaphore(url, idx) for idx, url in enumerate(urls)]
    results = await asyncio.gather(*tasks)
    
    total_time = asyncio.get_event_loop().time() - start_time
    
    # 统计结果
    success_count = sum(1 for r in results if r.get("status") == 200)
    print(f"\n完成！总耗时: {total_time:.2f}s | 成功: {success_count}/{len(urls)} | QPS: {len(urls)/total_time:.2f}")


async def file_upload_demo():
    """
    演示文件上传
    """
    print("\n" + "=" * 60)
    print("演示文件上传")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 1. 上传文本文件
        print("\n1. 上传文本文件:")
        form_data = aiohttp.FormData()
        form_data.add_field("file", "Hello, Aiohttp!", filename="test.txt", content_type="text/plain")
        form_data.add_field("description", "测试文件")
        
        async with session.post("https://httpbin.org/post", data=form_data) as resp:
            result = await resp.json()
            print(f"状态码: {resp.status}")
            print(f"文件字段: {list(result['files'].keys())}")
            print(f"文件内容: {result['files']['file']}")
        
        # 2. 上传二进制数据
        print("\n2. 上传二进制数据:")
        binary_data = b"\x00\x01\x02\x03\x04\x05"
        form_data = aiohttp.FormData()
        form_data.add_field("binary", binary_data, filename="data.bin", content_type="application/octet-stream")
        
        async with session.post("https://httpbin.org/post", data=form_data) as resp:
            result = await resp.json()
            print(f"状态码: {resp.status}")
            print(f"二进制文件上传成功")


async def streaming_response_demo():
    """
    演示流式响应处理
    """
    print("\n" + "=" * 60)
    print("演示流式响应处理")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        print("\n1. 流式读取大型响应:")
        async with session.get("https://httpbin.org/stream/5") as resp:
            print(f"状态码: {resp.status}")
            print(f"响应内容:")
            async for line in resp.content:  # 流式读取
                if line:  # 跳过空行
                    print(f"  {line.decode('utf-8').strip()}")


async def web_socket_demo():
    """
    演示WebSocket客户端
    """
    print("\n" + "=" * 60)
    print("演示WebSocket客户端")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect("wss://echo.websocket.events") as ws:
                print("WebSocket连接成功")
                
                # 发送消息
                test_messages = ["Hello WebSocket!", "How are you?", "Goodbye!"]
                
                for msg in test_messages:
                    await ws.send_str(msg)
                    print(f"\n发送: {msg}")
                    
                    # 接收消息
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            print(f"接收: {msg.data}")
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            print("连接已关闭")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"WebSocket错误: {ws.exception()}")
                            break
                
                await ws.close()
                print("\nWebSocket连接已关闭")
    except Exception as e:
        print(f"WebSocket连接失败: {e}")


async def main():
    """
    主函数，运行所有演示
    """
    print("开始学习 asyncio + aiohttp 高级特性")
    print("=" * 80)
    
    # 运行各个演示
    await http_methods_demo()
    await session_management_demo()
    await timeout_and_error_handling()
    await semaphore_concurrency_control()
    await file_upload_demo()
    await streaming_response_demo()
    await web_socket_demo()
    
    print("\n" + "=" * 80)
    print("所有演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
