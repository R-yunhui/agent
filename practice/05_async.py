"""
异步编程，单线程多协程
asyncio 是并发而不是并行。它在单线程内通过协程切换实现并发，适合IO密集型任务。真正的并行需要多进程。
"""
import asyncio
import time

import aiohttp
from faker import Faker

fake = Faker(
    locale="zh_CN",
)


async def say_hello(name: str) -> str:
    print(f"Hello, {name}!")
    # 遇到 io 操作时，会让出控制权，等待 io 完成后继续执行，在这时间内，其他协程可以执行
    await asyncio.sleep(1)
    print(f"Goodbye, {name}!")
    return f"{name} done"


async def task(name, delay):
    print(f"{name} 开始执行，等待 {delay} 秒")
    await asyncio.sleep(delay)
    print(f"{name} 执行完成")
    return f"{name} done"


async def multi_task():
    start_time = time.time()
    names = [fake.name() for _ in range(3)]
    delays = [fake.random_int(min=1, max=3) for _ in range(3)]
    # 两种写法，效果相同
    tasks = [asyncio.create_task(task(names[i], delays[i])) for i in range(3)]
    results = await asyncio.gather(*tasks)

    # results = await asyncio.gather(
    #     task(names[0], delays[0]),
    #     task(names[1], delays[1]),
    #     task(names[2], delays[2]),
    # )
    print(f"所有任务执行完成，耗时 {time.time() - start_time:.2f} 秒")
    return results


async def wait_demo():
    """
    学习 asyncio.wait() 的一些用法
    """
    start_time = time.time()
    tasks = [asyncio.create_task(task(fake.name(), fake.random_int(min=1, max=3))) for _ in range(3)]
    # 等待第一个任务完成
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    print(f"第一个完成的任务: {done.pop().result()}")
    print(f"还有 {len(pending)} 个任务未完成")

    # 等待剩下的完成
    done, pending = await asyncio.wait(pending)
    print(f"剩下的任务完成: {[t.result() for t in done]}")
    print(f"还有 {len(pending)} 个任务未完成")
    print(f"所有任务执行完成，耗时 {time.time() - start_time:.2f} 秒")


async def as_competed_demo():
    """
    as_completed 按完成顺序处理
    """
    start_time = time.time()
    tasks = [asyncio.create_task(task(fake.name(), fake.random_int(min=1, max=3))) for _ in range(3)]
    for done_task in asyncio.as_completed(tasks):
        result = await done_task
        print(f"任务完成: {result}")
    print(f"所有任务执行完成，耗时 {time.time() - start_time:.2f} 秒")


async def aslow_task(name, delay):
    await asyncio.sleep(delay)
    return f"{name} done"


async def time_out_demo():
    """
    学习 asyncio.wait_for() 的一些用法
    """
    start_time = time.time()
    try:
        result = await asyncio.wait_for(aslow_task(fake.name(), fake.random_int(min=3, max=10)), timeout=2)
        print(f"任务完成: {result}")
    except asyncio.TimeoutError:
        print("超时了")
    else:
        print(f"所有任务执行完成，耗时 {time.time() - start_time:.2f} 秒")


async def fetch(url, semaphore):
    async with semaphore:  # 限制同时运行的数量
        print(f"请求 {url}")
        await asyncio.sleep(1)
        return f"{url} done"


async def asemaphore_demo():
    semaphore = asyncio.Semaphore(3)  # 最多3个并发

    urls = [fake.url() for i in range(10)]
    tasks = [fetch(url, semaphore) for url in urls]
    results = await asyncio.gather(*tasks)
    print(results)


async def fetch_two(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as response:
        return await response.text()


async def actually_example():
    """
    实际场景中，通过 aiohttp 库发起异步请求时，也需要限制并发数量
    """
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
    ]

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_two(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        for url, result in zip(urls, results):
            print(f"{url} 长度: {len(result)}")


async def main():
    # print("=" * 20)
    # print(f"简单的异步函数调用")
    # result = await say_hello(fake.name())
    # print(result)

    # print("=" * 20)
    # print(f"多个异步任务调用")
    # results = await multi_task()
    # print(results)

    # print("=" * 20)
    # print(f"等待多个异步任务完成")
    # await wait_demo()

    # print("=" * 20)
    # print(f"按完成顺序处理异步任务")
    # await as_competed_demo()

    # print("=" * 20)
    # print(f"异步任务超时处理")
    # await time_out_demo()

    # print("=" * 20)
    # print(f"异步任务并发控制")
    # await asemaphore_demo()

    print("=" * 20)
    print(f"实际场景中，通过 aiohttp 库发起异步请求")
    await actually_example()


if __name__ == "__main__":
    """
    async def 定义的函数调用后返回协程对象，不会立即执行
    await 只能在 async def 内部使用
    asyncio.run() 是程序入口，启动事件循环
    """
    asyncio.run(main())
