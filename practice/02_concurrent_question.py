"""
并发问题 + 锁
"""
from threading import Thread, Lock, Semaphore
import time

counter = 0

# 不可重入锁。如果一个线程已经获取了锁，再次获取锁会阻塞线程，而不是死循环等待。
# RLock 可重入锁。如果一个线程已经获取了锁，再次获取锁不会阻塞线程，而是增加锁的计数器。
# 只有当锁的计数器为 0 时，线程才会被允许释放锁。
lock = Lock()

# 最多允许 2 个线程同时执行
semaphore = Semaphore(2)


def increment() -> int:
    global counter
    with lock:  # 加锁，确保每次只有一个线程可以执行 counter += 1
        for _ in range(1000000):
            counter += 1  # 非原子操作，可能会被中断


def worker(name: str):
    with semaphore:  # 最多允许 2 个线程同时执行
        print(f"{name} 获得资源")
        time.sleep(2)
        print(f"{name} 释放资源")


def test_semaphore():
    threads = []
    for _ in range(4):
        t = Thread(target=worker, args=(f"线程 {_}",))
        threads.append(t)
        t.start()

    # 等待所有线程的任务执行完毕
    for t in threads:
        t.join()


def run_concurrent():
    threads = []
    for _ in range(4):
        t = Thread(target=increment)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()  # 等待所有线程的任务执行完毕


def print_num():
    """
    顺序循环打印数字 1 2 3 1 2 3 ...
    """
    num = 1
    semaphore_two = Semaphore(1)

    for _ in range(102):
        with semaphore_two:
            if num == 1:
                print(num, end=" ")
                num += 1
            elif num == 2:
                print(num, end=" ")
                num += 1
            elif num == 3:
                print(num, end=" ")
                num = 1
                print()


def main():
    """
    主函数，演示并发执行任务
    """
    # print("=" * 30)
    # print("并发执行任务")
    # run_concurrent()
    # print(f"最终 counter 值: {counter}")
    # print("=" * 30)
    #
    # print("=" * 30)
    # print("测试信号量")
    # test_semaphore()
    # print("=" * 30)

    # print("=" * 30)
    # print("循环打印数字1 2 3")
    # print_num()
    # print("=" * 30)


if __name__ == "__main__":
    main()
