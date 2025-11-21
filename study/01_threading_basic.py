"""
Python 线程基础学习 - 对应 Java 的 Thread 类

Python 的 threading.Thread 类似于 Java 的 Thread 类
主要区别：
1. Python 有 GIL (Global Interpreter Lock)，导致 CPU 密集型任务无法真正并行
2. 但对于 I/O 密集型任务（网络请求、文件读写等），多线程仍然有效
"""

import threading
import time
from typing import List


# 方式1: 继承 Thread 类（类似 Java 的 extends Thread）
class MyThread(threading.Thread):
    """自定义线程类 - 类似 Java: class MyThread extends Thread"""

    def __init__(self, name: str, delay: int):
        super().__init__()
        self.thread_name = name
        self.delay = delay

    def run(self):
        """重写 run 方法 - 类似 Java 的 @Override public void run()"""
        print(f"线程 {self.thread_name} 开始执行")
        for i in range(3):
            time.sleep(self.delay)
            print(f"{self.thread_name}: 第 {i + 1} 次执行")
        print(f"线程 {self.thread_name} 执行完毕")


# 方式2: 使用函数创建线程（类似 Java 的 Runnable 接口）
def worker_function(name: str, delay: int) -> None:
    """工作函数 - 类似 Java 的 Runnable"""
    print(f"Worker {name} 开始执行")
    for i in range(3):
        time.sleep(delay)
        print(f"Worker {name}: 第 {i + 1} 次执行")
    print(f"Worker {name} 执行完毕")


# 方式3: 使用 Lambda（Python 的特色，Java 8+ 也支持）
def demo_basic_threading():
    """基础线程示例"""
    print("=" * 50)
    print("示例1: 继承 Thread 类")
    print("=" * 50)

    # 创建线程（类似 Java: MyThread t1 = new MyThread("线程1", 1)）
    thread1 = MyThread("线程1", 1)
    thread2 = MyThread("线程2", 2)

    # 启动线程（类似 Java: t1.start()）
    thread1.start()
    thread2.start()

    # 等待线程结束（类似 Java: t1.join()）
    thread1.join()
    thread2.join()

    print("\n所有线程执行完毕\n")


def demo_function_threading():
    """使用函数创建线程"""
    print("=" * 50)
    print("示例2: 使用函数创建线程（Runnable 方式）")
    print("=" * 50)

    # 类似 Java: Thread t = new Thread(new Runnable() {...})
    # 或 Java 8+: Thread t = new Thread(() -> {...})
    thread1 = threading.Thread(target=worker_function, args=("A", 1))
    thread2 = threading.Thread(target=worker_function, args=("B", 1))

    # 设置为守护线程（类似 Java: t.setDaemon(true)）
    thread1.daemon = False  # 默认为 False

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    print("\n所有工作线程执行完毕\n")


# 线程同步：使用 Lock（类似 Java 的 synchronized 或 ReentrantLock）
class Counter:
    """线程安全的计数器"""

    def __init__(self):
        self.count = 0
        # 类似 Java: private final Lock lock = new ReentrantLock()
        self.lock = threading.Lock()

    def increment(self):
        """线程安全的自增操作"""
        # with lock 类似 Java 的 synchronized 块
        # Java: synchronized(lock) { ... }
        with self.lock:
            current = self.count
            time.sleep(0.0001)  # 模拟一些处理时间
            self.count = current + 1

    def get_count(self) -> int:
        """获取当前计数"""
        with self.lock:
            return self.count


def demo_thread_synchronization():
    """线程同步示例"""
    print("=" * 50)
    print("示例3: 线程同步（Lock）")
    print("=" * 50)

    counter = Counter()
    threads: List[threading.Thread] = []

    def increment_counter(counter: Counter, times: int):
        for _ in range(times):
            counter.increment()

    # 创建 10 个线程，每个线程自增 100 次
    for i in range(10):
        t = threading.Thread(target=increment_counter, args=(counter, 100))
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    print(f"最终计数: {counter.get_count()}")
    print(f"期望计数: 1000")
    print(f"结果{'正确' if counter.get_count() == 1000 else '错误'}（由于使用了 Lock）\n")


# 线程间通信：使用 Queue（类似 Java 的 BlockingQueue）
from queue import Queue


def demo_thread_communication():
    """线程间通信示例"""
    print("=" * 50)
    print("示例4: 线程间通信（Queue）")
    print("=" * 50)

    # 类似 Java: BlockingQueue<String> queue = new LinkedBlockingQueue<>(5)
    task_queue: Queue[str] = Queue(maxsize=5)

    def producer(queue: Queue, items: int):
        """生产者"""
        for i in range(items):
            item = f"任务-{i + 1}"
            queue.put(item)  # 类似 Java: queue.put(item)
            print(f"生产者: 生产了 {item}")
            time.sleep(0.5)
        queue.put(None)  # 发送结束信号
        print("生产者: 完成生产")

    def consumer(queue: Queue):
        """消费者"""
        while True:
            item = queue.get()  # 类似 Java: queue.take()
            if item is None:
                queue.task_done()
                break
            print(f"消费者: 消费了 {item}")
            time.sleep(1)
            queue.task_done()  # 标记任务完成
        print("消费者: 完成消费")

    # 创建生产者和消费者线程
    producer_thread = threading.Thread(target=producer, args=(task_queue, 5))
    consumer_thread = threading.Thread(target=consumer, args=(task_queue,))

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    consumer_thread.join()

    print("\n生产者-消费者示例完成\n")


def main():
    """主函数"""
    print("\n🎯 Python 线程基础学习\n")

    # 运行所有示例
    demo_basic_threading()
    demo_function_threading()
    demo_thread_synchronization()
    demo_thread_communication()

    print("✅ 所有示例执行完毕！")


if __name__ == "__main__":
    main()
