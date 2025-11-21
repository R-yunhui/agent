"""
Python 线程池学习 - 对应 Java 的 ExecutorService / ThreadPoolExecutor

Python 的 concurrent.futures.ThreadPoolExecutor 类似于：
- Java 的 ExecutorService
- Java 的 ThreadPoolExecutor
但使用更简单，API 更现代化
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, Future
from typing import List, Dict
import random


# 示例任务函数
def download_file(file_id: int) -> Dict[str, any]:
    """模拟下载文件（I/O 密集型任务）"""
    print(f"开始下载文件 {file_id}")
    # 模拟网络延迟
    time.sleep(random.uniform(1, 3))
    result = {
        "file_id": file_id,
        "size": random.randint(100, 1000),
        "status": "success"
    }
    print(f"完成下载文件 {file_id}")
    return result


def process_data(data: int) -> int:
    """模拟数据处理"""
    print(f"处理数据: {data}")
    time.sleep(1)
    result = data * 2
    print(f"数据 {data} 处理完成，结果: {result}")
    return result


def demo_basic_threadpool():
    """基础线程池示例"""
    print("=" * 50)
    print("示例1: 基础线程池使用")
    print("=" * 50)
    
    # 创建线程池，最多 3 个工作线程
    # 类似 Java: ExecutorService executor = Executors.newFixedThreadPool(3)
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交任务（类似 Java: Future<Integer> future = executor.submit(() -> {...})）
        future1: Future[int] = executor.submit(process_data, 10)
        future2: Future[int] = executor.submit(process_data, 20)
        future3: Future[int] = executor.submit(process_data, 30)
        
        # 获取结果（类似 Java: future.get()）
        # 这会阻塞直到任务完成
        result1 = future1.result()
        result2 = future2.result()
        result3 = future3.result()
        
        print(f"\n结果: {result1}, {result2}, {result3}\n")
    # with 语句结束时会自动调用 executor.shutdown(wait=True)
    # 类似 Java: executor.shutdown() + executor.awaitTermination()


def demo_map_function():
    """使用 map 批量执行任务"""
    print("=" * 50)
    print("示例2: 使用 map 批量处理")
    print("=" * 50)
    
    data_list = [1, 2, 3, 4, 5]
    
    # 类似 Java 8 的 Stream API:
    # List<Integer> results = dataList.stream()
    #     .parallel()
    #     .map(this::processData)
    #     .collect(Collectors.toList());
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # map 会按顺序返回结果
        results = executor.map(process_data, data_list)
        
        print(f"\n所有结果: {list(results)}\n")


def demo_as_completed():
    """使用 as_completed 处理完成的任务"""
    print("=" * 50)
    print("示例3: 使用 as_completed 处理任务（按完成顺序）")
    print("=" * 50)
    
    file_ids = [1, 2, 3, 4, 5]
    
    # 类似 Java 的 ExecutorCompletionService
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交所有任务
        futures: List[Future] = [
            executor.submit(download_file, file_id) 
            for file_id in file_ids
        ]
        
        # as_completed 返回已完成的 future（按完成顺序，不是提交顺序）
        # 类似 Java: CompletionService 的 take() 方法
        for future in as_completed(futures):
            try:
                result = future.result()
                print(f"获取到结果: 文件 {result['file_id']}, "
                      f"大小 {result['size']} KB")
            except Exception as e:
                print(f"任务执行失败: {e}")
        
        print()


def demo_wait_function():
    """使用 wait 等待任务完成"""
    print("=" * 50)
    print("示例4: 使用 wait 等待任务")
    print("=" * 50)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(download_file, i) for i in range(5)]
        
        # wait 返回两个集合: (done, not_done)
        # 类似 Java 的 invokeAll() 或手动检查 Future.isDone()
        done, not_done = wait(futures, timeout=5)
        
        print(f"已完成任务数: {len(done)}")
        print(f"未完成任务数: {len(not_done)}")
        
        # 处理已完成的任务
        for future in done:
            result = future.result()
            print(f"文件 {result['file_id']} 下载完成")
        
        print()


def task_with_exception(value: int) -> int:
    """可能抛出异常的任务"""
    print(f"处理值: {value}")
    if value == 3:
        raise ValueError(f"值 {value} 导致错误！")
    time.sleep(1)
    return value * 2


def demo_exception_handling():
    """异常处理示例"""
    print("=" * 50)
    print("示例5: 异常处理")
    print("=" * 50)
    
    values = [1, 2, 3, 4, 5]
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(task_with_exception, val): val 
            for val in values
        }
        
        for future in as_completed(futures):
            original_value = futures[future]
            try:
                # result() 会重新抛出任务中的异常
                # 类似 Java: future.get() throws ExecutionException
                result = future.result()
                print(f"值 {original_value} 处理成功，结果: {result}")
            except Exception as e:
                print(f"值 {original_value} 处理失败: {e}")
        
        print()


def demo_callback():
    """使用回调函数"""
    print("=" * 50)
    print("示例6: 添加回调函数")
    print("=" * 50)
    
    def done_callback(future: Future):
        """任务完成时的回调"""
        # 类似 Java 的 CompletableFuture.thenAccept()
        try:
            result = future.result()
            print(f"✅ 回调: 任务完成，结果 = {result}")
        except Exception as e:
            print(f"❌ 回调: 任务失败，错误 = {e}")
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(process_data, 100)
        future2 = executor.submit(task_with_exception, 3)
        
        # 添加回调（任务完成后自动调用）
        future1.add_done_callback(done_callback)
        future2.add_done_callback(done_callback)
        
        # 等待所有任务完成
        wait([future1, future2])
        
        print()


def demo_advanced_pattern():
    """高级使用模式：生产者-消费者"""
    print("=" * 50)
    print("示例7: 高级模式 - 动态任务提交")
    print("=" * 50)
    
    def worker(task_id: int) -> str:
        """工作任务"""
        time.sleep(random.uniform(0.5, 1.5))
        return f"任务 {task_id} 完成"
    
    # 使用线程池实现动态任务提交
    # 类似 Java 的自定义 ExecutorService 模式
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        
        # 动态提交任务
        for i in range(10):
            future = executor.submit(worker, i+1)
            futures.append(future)
            print(f"提交任务 {i+1}")
        
        # 实时处理完成的任务
        for future in as_completed(futures):
            result = future.result()
            print(f"收到结果: {result}")
        
        print()


def main():
    """主函数"""
    print("\n🎯 Python 线程池学习\n")
    
    # 运行所有示例
    demo_basic_threadpool()
    demo_map_function()
    demo_as_completed()
    demo_wait_function()
    demo_exception_handling()
    demo_callback()
    demo_advanced_pattern()
    
    print("✅ 所有示例执行完毕！")
    print("\n💡 小贴士:")
    print("1. ThreadPoolExecutor 适合 I/O 密集型任务")
    print("2. CPU 密集型任务应使用 ProcessPoolExecutor（绕过 GIL）")
    print("3. 使用 with 语句可以自动管理线程池生命周期")
    print("4. as_completed 可以按完成顺序处理结果，提高响应性")


if __name__ == "__main__":
    main()
