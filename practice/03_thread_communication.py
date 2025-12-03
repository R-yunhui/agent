"""
线程间通信
"""
import random
import time
from threading import Thread, Event, Condition

# 用于线程间通信，一个线程发信号，其他线程等待：
event = Event()

# 条件变量
# 更灵活的线程协调，经典的生产者-消费者模式
condition = Condition()

queue = []


def waiter(name):
    print(f"{name} 等待事件...")
    event.wait()  # 无限阻塞，等待事件通知
    print(f"{name} 收到事件通知, 继续执行")


def notifier(name):
    time.sleep(2)
    print(f"{name} 发送事件通知")
    event.set()  # 发送事件通知


def producer():
    for i in range(10):
        time.sleep(random.random() * 2)
        with condition:
            item = f"产品-{i}"
            queue.append(item)
            print(f"producer 生产 {item}, 队列长度: {len(queue)}")
            condition.notify()  # 通知消费者线程


def consumer():
    while True:
        with condition:
            while not queue:
                condition.wait()  # 等待生产者生产产品
            item = queue.pop(0)
            print(f"consumer 消费 {item}, 队列长度: {len(queue)}")


def test_condition():
    """
    测试条件变量
    """
    producer_thread = Thread(target=producer)
    # 消费者设为守护线程，等待主线程执行完毕之后自动退出
    consumer_thread = Thread(target=consumer, daemon=True)

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    # 在等待 2s 之后，主线程会自动退出，导致消费者线程也退出
    print("main 等待 2s 后退出")
    time.sleep(2)


def test_event():
    threads = []
    for _ in range(3):
        t = Thread(target=waiter, args=(f"等待线程 {_}",))
        threads.append(t)
        t.start()

    print("main 准备发送事件通知")
    time.sleep(2)
    notifier("main")

    for t in threads:
        t.join()  # 等待所有线程的任务执行完毕


def main():
    # print("=" * 30)
    # print("测试事件")
    # test_event()
    # print("\n" + "=" * 30)

    print("=" * 30)
    print("测试条件变量")
    test_condition()
    print("=" * 30)


if __name__ == "__main__":
    main()
