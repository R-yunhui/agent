"""
并发（Concurrency）
并行（Parallelism）
"""
import asyncio
from threading import Thread
from multiprocessing import Process
import time


def log_time_decorator(func):
    def wrapper():
        start_time = time.time()
        result = func()
        end_time = time.time()
        print(f"{func.__name__} 耗时: {end_time - start_time:.2f} 秒")
        return result

    return wrapper


def io_task():
    """
    模拟IO密集型任务，如网络请求、文件读写等
    """
    time.sleep(2)


def cpu_task():
    """
    模拟CPU密集型任务，如复杂的计算、排序等
    """
    result = 0
    for _ in range(100000000):
        result += 1
    return result


@log_time_decorator
def run_current():
    """
    并发执行任务
    """
    threads = []
    for _ in range(4):
        t = Thread(target=cpu_task)
        threads.append(t)
        t.start()

    """
    由于 py 底层的 GIL 锁的存在，导致并发执行的任务只能在一个线程中执行，无法真正实现并行。
    """
    for t in threads:
        t.join()  # 等待所有线程的任务执行完毕


@log_time_decorator
def run_serial():
    """
    顺序执行任务
    """
    for _ in range(4):
        cpu_task()


class RunWorker(Thread):

    def __init__(self, name: str, count: int):
        super().__init__()
        self.name = name
        self.count = count

    def run(self):
        for i in range(self.count):
            time.sleep(1)
            print(f"{self.name} 执行第 {i + 1} 次任务")


@log_time_decorator
def run_worker():
    """
    并发执行任务
    """
    threads = []
    for i in range(4):
        t = RunWorker(f"线程{i + 1}", 3)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()  # 等待所有线程的任务执行完毕


async def arun_current():
    """
    并行执行任务
    """
    start_time = time.time()
    tasks = []
    for _ in range(4):
        tasks.append(acpu_task())

    # 协程并行执行任务
    """
    协程可以在一个线程中并发执行，利用空闲时间执行其他任务，但是对于 CPU 密集型任务，由于 GIL 锁的存在，无法真正实现并行。
    """
    result = await asyncio.gather(*tasks)
    print(result)
    end_time = time.time()
    print(f"并行执行任务 耗时: {end_time - start_time:.2f} 秒")


async def acpu_task():
    """
    模拟可等待的CPU密集型任务，如复杂的计算、排序等
    """
    result = 0
    for _ in range(100000000):
        result += 1
    return result


def run_multi_process():
    """
    使用多进程并行执行CPU密集型任务。
    每个进程有自己的Python解释器和GIL，可以被操作系统调度到不同CPU核心上，
    从而实现真正的并行计算，能显著缩短CPU密集型任务的执行时间。
    """
    start_time = time.time()

    processes = []
    for _ in range(4):
        p = Process(target=cpu_task)
        processes.append(p)
        p.start()

    for p in processes:
        p.join()  # 等待所有进程的任务执行完毕
    end_time = time.time()
    print(f"多进程执行任务 耗时: {end_time - start_time:.2f} 秒")


def main():
    """
    主函数，演示并发执行任务
    """
    print("=" * 30)
    print("并发执行任务")
    run_current()

    print("\n" + "=" * 30)
    print("顺序执行任务")
    run_serial()
    #
    # print("\n" + "=" * 30)
    # print("继承Thread 重写 run 方法")
    # run_worker()
    # print("=" * 30)

    print("\n" + "=" * 30)
    print("并行执行任务")
    asyncio.run(arun_current())
    print("=" * 30)

    print("\n" + "=" * 30)
    print("多进程执行任务")
    run_multi_process()
    print("=" * 30)


if __name__ == "__main__":
    main()
