"""
Python 异步编程学习 - asyncio

asyncio 是 Python 的异步 I/O 框架，类似但不完全等同于：
- Java 的 CompletableFuture
- Java 的 Project Loom (Virtual Threads)
- JavaScript 的 async/await

主要概念：
1. async def - 定义协程函数（coroutine）
2. await - 等待协程完成
3. asyncio.create_task() - 创建任务
4. asyncio.gather() - 并发执行多个任务
"""

import asyncio
import time
from typing import List
import aiohttp  # 需要安装: pip install aiohttp


# 基础协程示例
async def hello_coroutine(name: str, delay: int) -> str:
    """
    基础协程函数
    
    async def 类似 Java 的 CompletableFuture.supplyAsync()
    但语法更简洁
    """
    print(f"Hello {name}，开始等待 {delay} 秒")
    
    # await 会挂起当前协程，让出控制权给事件循环
    # 类似 Java 的 CompletableFuture.get()，但不会阻塞线程
    await asyncio.sleep(delay)
    
    result = f"{name} 完成了！"
    print(result)
    return result


async def demo_basic_coroutine():
    """示例1: 基础协程使用"""
    print("=" * 50)
    print("示例1: 基础协程")
    print("=" * 50)
    
    # 直接 await 协程（按顺序执行）
    result1 = await hello_coroutine("任务1", 2)
    result2 = await hello_coroutine("任务2", 1)
    
    print(f"结果: {result1}, {result2}\n")


async def demo_concurrent_tasks():
    """示例2: 并发执行多个任务"""
    print("=" * 50)
    print("示例2: 并发执行任务")
    print("=" * 50)
    
    start_time = time.time()
    
    # 创建任务（类似 Java: CompletableFuture.supplyAsync()）
    # asyncio.create_task() 会立即开始执行协程
    task1 = asyncio.create_task(hello_coroutine("并发任务1", 2))
    task2 = asyncio.create_task(hello_coroutine("并发任务2", 2))
    task3 = asyncio.create_task(hello_coroutine("并发任务3", 2))
    
    # 等待所有任务完成
    results = await asyncio.gather(task1, task2, task3)
    
    elapsed = time.time() - start_time
    print(f"所有任务完成，耗时: {elapsed:.2f} 秒")
    print(f"结果: {results}\n")


async def fetch_data(url: str, delay: int) -> dict:
    """模拟异步获取数据"""
    print(f"开始获取: {url}")
    await asyncio.sleep(delay)
    data = {
        "url": url,
        "data": f"来自 {url} 的数据",
        "delay": delay
    }
    print(f"完成获取: {url}")
    return data


async def demo_gather_vs_tasks():
    """示例3: gather 的不同用法"""
    print("=" * 50)
    print("示例3: asyncio.gather() 用法")
    print("=" * 50)
    
    # 方式1: 直接传入协程
    # 类似 Java: CompletableFuture.allOf(futures).join()
    results = await asyncio.gather(
        fetch_data("api/users", 1),
        fetch_data("api/posts", 2),
        fetch_data("api/comments", 1)
    )
    
    print(f"获取到 {len(results)} 个结果")
    for result in results:
        print(f"  - {result['url']}: {result['data']}")
    
    print()


async def demo_gather_with_exceptions():
    """示例4: 异常处理"""
    print("=" * 50)
    print("示例4: 异常处理")
    print("=" * 50)
    
    async def task_may_fail(task_id: int) -> int:
        """可能失败的任务"""
        await asyncio.sleep(1)
        if task_id == 2:
            raise ValueError(f"任务 {task_id} 失败了！")
        return task_id * 10
    
    # 方式1: gather 默认会传播第一个异常
    try:
        results = await asyncio.gather(
            task_may_fail(1),
            task_may_fail(2),
            task_may_fail(3)
        )
        print(f"结果: {results}")
    except ValueError as e:
        print(f"捕获到异常: {e}")
    
    # 方式2: 使用 return_exceptions=True 收集所有结果和异常
    # 类似 Java 的 CompletableFuture.handle()
    results = await asyncio.gather(
        task_may_fail(1),
        task_may_fail(2),
        task_may_fail(3),
        return_exceptions=True
    )
    
    print("\n使用 return_exceptions=True:")
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"  任务 {i}: 失败 - {result}")
        else:
            print(f"  任务 {i}: 成功 - {result}")
    
    print()


async def demo_wait_for_timeout():
    """示例5: 超时控制"""
    print("=" * 50)
    print("示例5: 超时控制")
    print("=" * 50)
    
    async def slow_operation() -> str:
        """慢速操作"""
        print("开始慢速操作...")
        await asyncio.sleep(5)
        return "操作完成"
    
    # asyncio.wait_for() 设置超时
    # 类似 Java: future.get(timeout, TimeUnit.SECONDS)
    try:
        result = await asyncio.wait_for(slow_operation(), timeout=2.0)
        print(f"结果: {result}")
    except asyncio.TimeoutError:
        print("操作超时！")
    
    print()


async def demo_task_cancellation():
    """示例6: 任务取消"""
    print("=" * 50)
    print("示例6: 任务取消")
    print("=" * 50)
    
    async def cancellable_task(task_id: int) -> str:
        """可取消的任务"""
        try:
            print(f"任务 {task_id} 开始")
            await asyncio.sleep(5)
            return f"任务 {task_id} 完成"
        except asyncio.CancelledError:
            print(f"任务 {task_id} 被取消")
            raise  # 重要：需要重新抛出 CancelledError
    
    # 创建任务
    task = asyncio.create_task(cancellable_task(1))
    
    # 等待一小段时间后取消
    await asyncio.sleep(1)
    task.cancel()  # 类似 Java: future.cancel(true)
    
    try:
        await task
    except asyncio.CancelledError:
        print("任务已取消")
    
    print()


async def demo_queue():
    """示例7: 异步队列（生产者-消费者）"""
    print("=" * 50)
    print("示例7: 异步队列")
    print("=" * 50)
    
    # 类似 Java 的 BlockingQueue，但是异步的
    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=3)
    
    async def producer(queue: asyncio.Queue, items: int):
        """生产者"""
        for i in range(items):
            item = f"任务-{i+1}"
            await queue.put(item)  # 异步放入队列
            print(f"生产者: 生产了 {item}")
            await asyncio.sleep(0.5)
        await queue.put(None)  # 结束信号
        print("生产者: 完成")
    
    async def consumer(queue: asyncio.Queue):
        """消费者"""
        while True:
            item = await queue.get()  # 异步获取
            if item is None:
                queue.task_done()
                break
            print(f"消费者: 消费了 {item}")
            await asyncio.sleep(1)
            queue.task_done()
        print("消费者: 完成")
    
    # 并发运行生产者和消费者
    await asyncio.gather(
        producer(queue, 5),
        consumer(queue)
    )
    
    print()


async def demo_semaphore():
    """示例8: 信号量（限制并发数）"""
    print("=" * 50)
    print("示例8: 信号量限制并发")
    print("=" * 50)
    
    # 创建信号量，最多允许 2 个并发
    # 类似 Java: Semaphore semaphore = new Semaphore(2)
    semaphore = asyncio.Semaphore(2)
    
    async def limited_task(task_id: int):
        """受限制的任务"""
        async with semaphore:  # 获取信号量
            print(f"任务 {task_id} 开始执行")
            await asyncio.sleep(2)
            print(f"任务 {task_id} 执行完毕")
            return task_id
    
    # 创建 5 个任务，但同时只有 2 个在执行
    tasks = [limited_task(i) for i in range(1, 6)]
    results = await asyncio.gather(*tasks)
    
    print(f"所有任务完成: {results}\n")


async def demo_async_comprehension():
    """示例9: 异步推导式"""
    print("=" * 50)
    print("示例9: 异步推导式")
    print("=" * 50)
    
    async def get_number(n: int) -> int:
        """异步获取数字"""
        await asyncio.sleep(0.1)
        return n * 2
    
    # 异步列表推导式（Python 3.6+）
    # 注意：这会依次执行，不是并发
    results = [await get_number(i) for i in range(5)]
    print(f"异步推导结果: {results}")
    
    # 如需并发执行，使用 gather
    results_concurrent = await asyncio.gather(
        *[get_number(i) for i in range(5)]
    )
    print(f"并发执行结果: {results_concurrent}\n")


async def main_async():
    """主异步函数"""
    print("\n🎯 Python 异步编程学习（asyncio）\n")
    
    # 运行所有示例
    await demo_basic_coroutine()
    await demo_concurrent_tasks()
    await demo_gather_vs_tasks()
    await demo_gather_with_exceptions()
    await demo_wait_for_timeout()
    await demo_task_cancellation()
    await demo_queue()
    await demo_semaphore()
    await demo_async_comprehension()
    
    print("✅ 所有示例执行完毕！")
    print("\n💡 小贴士:")
    print("1. async/await 只是语法糖，底层是协程和事件循环")
    print("2. asyncio 适合 I/O 密集型任务，不适合 CPU 密集型")
    print("3. 协程之间是协作式调度，必须使用 await 让出控制权")
    print("4. asyncio.gather() 用于并发执行，asyncio.wait() 更灵活")
    print("5. Python 的 GIL 依然存在，asyncio 不能利用多核 CPU")


# 运行异步主函数的几种方式
if __name__ == "__main__":
    # 方式1: Python 3.7+ 推荐方式
    asyncio.run(main_async())
    
    # 方式2: 旧版本兼容方式
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main_async())
    # loop.close()
