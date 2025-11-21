"""
对比：线程 vs 线程池 vs 异步编程

这个文件对比三种并发方式的性能和适用场景
"""

import time
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List


# ========== 测试任务 ==========

def io_bound_task_sync(task_id: int) -> dict:
    """I/O 密集型任务（同步版本）"""
    time.sleep(0.5)  # 模拟 I/O 操作（网络请求、文件读取等）
    return {"task_id": task_id, "result": task_id * 2}


async def io_bound_task_async(task_id: int) -> dict:
    """I/O 密集型任务（异步版本）"""
    await asyncio.sleep(0.5)  # 异步 I/O
    return {"task_id": task_id, "result": task_id * 2}


def cpu_bound_task(n: int) -> int:
    """CPU 密集型任务"""
    # 计算前 n 个数的平方和
    result = sum(i * i for i in range(n))
    return result


# ========== 方式1: 顺序执行（基准） ==========

def sequential_execution(task_count: int = 10):
    """顺序执行（单线程）"""
    print("=" * 50)
    print("方式1: 顺序执行")
    print("=" * 50)
    
    start_time = time.time()
    results = []
    
    for i in range(task_count):
        result = io_bound_task_sync(i)
        results.append(result)
    
    elapsed = time.time() - start_time
    print(f"完成 {task_count} 个任务，耗时: {elapsed:.2f} 秒")
    print(f"平均每个任务: {elapsed/task_count:.2f} 秒\n")
    
    return elapsed


# ========== 方式2: 多线程 ==========

def multi_threading(task_count: int = 10):
    """使用多线程"""
    print("=" * 50)
    print("方式2: 多线程（threading.Thread）")
    print("=" * 50)
    
    start_time = time.time()
    results = []
    threads: List[threading.Thread] = []
    
    def worker(task_id: int):
        result = io_bound_task_sync(task_id)
        results.append(result)
    
    # 创建并启动线程
    for i in range(task_count):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    print(f"完成 {task_count} 个任务，耗时: {elapsed:.2f} 秒")
    print(f"提速: {sequential_execution.__name__} 的 {task_count * 0.5 / elapsed:.2f}x\n")
    
    return elapsed


# ========== 方式3: 线程池 ==========

def thread_pool_execution(task_count: int = 10):
    """使用线程池"""
    print("=" * 50)
    print("方式3: 线程池（ThreadPoolExecutor）")
    print("=" * 50)
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        # 使用 map 批量执行
        results = list(executor.map(io_bound_task_sync, range(task_count)))
    
    elapsed = time.time() - start_time
    print(f"完成 {task_count} 个任务，耗时: {elapsed:.2f} 秒")
    print(f"提速: 顺序执行的 {task_count * 0.5 / elapsed:.2f}x\n")
    
    return elapsed


# ========== 方式4: 异步编程 ==========

async def async_execution(task_count: int = 10):
    """使用异步编程"""
    print("=" * 50)
    print("方式4: 异步编程（asyncio）")
    print("=" * 50)
    
    start_time = time.time()
    
    # 创建所有任务
    tasks = [io_bound_task_async(i) for i in range(task_count)]
    
    # 并发执行
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    print(f"完成 {task_count} 个任务，耗时: {elapsed:.2f} 秒")
    print(f"提速: 顺序执行的 {task_count * 0.5 / elapsed:.2f}x\n")
    
    return elapsed


# ========== CPU 密集型任务对比 ==========

def compare_cpu_bound():
    """对比 CPU 密集型任务"""
    print("=" * 70)
    print("CPU 密集型任务对比")
    print("=" * 70)
    
    n = 1000000
    task_count = 4
    
    # 顺序执行
    print("\n1. 顺序执行 CPU 密集型任务:")
    start = time.time()
    results = [cpu_bound_task(n) for _ in range(task_count)]
    seq_time = time.time() - start
    print(f"   耗时: {seq_time:.2f} 秒")
    
    # 线程池（受 GIL 限制，可能更慢！）
    print("\n2. 线程池 CPU 密集型任务:")
    start = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(cpu_bound_task, [n] * task_count))
    thread_time = time.time() - start
    print(f"   耗时: {thread_time:.2f} 秒")
    print(f"   ⚠️ 由于 GIL，多线程可能更慢！")
    
    # ProcessPoolExecutor（真正的并行）
    from concurrent.futures import ProcessPoolExecutor
    print("\n3. 进程池 CPU 密集型任务:")
    start = time.time()
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(cpu_bound_task, [n] * task_count))
    process_time = time.time() - start
    print(f"   耗时: {process_time:.2f} 秒")
    print(f"   ✅ 提速: {seq_time / process_time:.2f}x")
    
    print()


# ========== 综合对比 ==========

def comprehensive_comparison():
    """综合性能对比"""
    print("\n" + "=" * 70)
    print("🎯 综合性能对比：I/O 密集型任务")
    print("=" * 70 + "\n")
    
    task_count = 20
    
    # 1. 顺序执行
    seq_time = sequential_execution(task_count)
    
    # 2. 多线程
    mt_time = multi_threading(task_count)
    
    # 3. 线程池
    tp_time = thread_pool_execution(task_count)
    
    # 4. 异步
    async_time = asyncio.run(async_execution(task_count))
    
    # 结果汇总
    print("=" * 70)
    print("📊 性能对比总结（I/O 密集型任务）")
    print("=" * 70)
    print(f"任务数量: {task_count}，每个任务耗时: 0.5 秒\n")
    print(f"{'方式':<20} {'耗时(秒)':<12} {'提速':<12} {'推荐度'}")
    print("-" * 70)
    print(f"{'顺序执行':<20} {seq_time:<12.2f} {'1.00x':<12} {'⭐'}")
    print(f"{'多线程':<20} {mt_time:<12.2f} {f'{seq_time/mt_time:.2f}x':<12} {'⭐⭐⭐'}")
    print(f"{'线程池':<20} {tp_time:<12.2f} {f'{seq_time/tp_time:.2f}x':<12} {'⭐⭐⭐⭐'}")
    print(f"{'异步(asyncio)':<20} {async_time:<12.2f} {f'{seq_time/async_time:.2f}x':<12} {'⭐⭐⭐⭐⭐'}")
    
    print("\n" + "=" * 70)
    print("💡 选择建议")
    print("=" * 70)
    print("""
I/O 密集型任务（网络请求、文件读写、数据库查询）:
  1️⃣ 首选: asyncio - 性能最好，内存开销小
  2️⃣ 次选: ThreadPoolExecutor - 易用，性能好
  3️⃣ 备选: 多线程 - 适合简单场景

CPU 密集型任务（数据处理、图像处理、科学计算）:
  1️⃣ 首选: ProcessPoolExecutor - 绕过 GIL，真正并行
  2️⃣ 备选: 多进程 multiprocessing
  ❌ 不推荐: 线程或 asyncio - 受 GIL 限制

混合型任务:
  1️⃣ 组合使用: asyncio + ProcessPoolExecutor
  2️⃣ asyncio 处理 I/O，ProcessPoolExecutor 处理 CPU
    """)


# ========== 实战示例：爬虫场景 ==========

async def demo_web_scraping_pattern():
    """实战：网页爬虫模式"""
    print("=" * 70)
    print("🕷️ 实战示例：网页爬虫模式")
    print("=" * 70)
    
    async def fetch_url(url: str) -> dict:
        """模拟抓取网页"""
        print(f"抓取: {url}")
        await asyncio.sleep(0.5)  # 模拟网络请求
        return {"url": url, "content": f"{url} 的内容", "status": 200}
    
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
        "https://example.com/page4",
        "https://example.com/page5",
    ]
    
    # 使用 asyncio 并发抓取
    start = time.time()
    results = await asyncio.gather(*[fetch_url(url) for url in urls])
    elapsed = time.time() - start
    
    print(f"\n抓取完成 {len(results)} 个页面，耗时: {elapsed:.2f} 秒")
    print("✅ 使用 asyncio + aiohttp 是爬虫的最佳实践\n")


def main():
    """主函数"""
    # I/O 密集型任务对比
    comprehensive_comparison()
    
    # CPU 密集型任务对比
    compare_cpu_bound()
    
    # 实战示例
    asyncio.run(demo_web_scraping_pattern())
    
    print("=" * 70)
    print("✅ 所有对比测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
