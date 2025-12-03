"""
线程池相关
"""
import time

from faker import Faker
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置 locale 为中文
fake = Faker(
    locale="zh_CN",
)


def task(name: str) -> str:
    print(f"{name} 开始执行...")
    time.sleep(1)
    print(f"{name} 执行完毕")
    return fake.name_male()


def thread_pool_one():
    """
    测试线程池，提交任务
    """
    with ThreadPoolExecutor(max_workers=2) as executor:
        for i in range(2):
            name = f"任务{i}"
            future = executor.submit(task, name)
            print(f"{name} 的执行结果: {future.result()}")

    print("所有任务执行完毕")


def send_email(email: str) -> str:
    execute_time = fake.random_int(min=2, max=5)
    print(f"发送邮件到 {email}, 需执行时间: {execute_time} 秒")
    time.sleep(execute_time)
    return email


def thread_pool_two():
    """
    测试线程池，批量提交任务
    """
    emails = [fake.email() for _ in range(4)]
    print(f"待发送的邮件列表: {emails}")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(send_email, email) for email in emails]
        # as_completed返回已完成的future，谁先完成谁先返回
        for future in as_completed(futures):
            print(f"邮件发送成功 {future.result()}")
    print("所有邮件发送完毕")


def thread_pool_three():
    """
    线程池的 map方法
    更简洁的批量处理方式
    """
    emails = [fake.email() for _ in range(4)]
    print(f"待发送的邮件列表: {emails}")
    with ThreadPoolExecutor(max_workers=4) as executor:
        # map返回结果的迭代器，顺序和输入一致
        results = executor.map(send_email, emails)
        for result in results:
            print(f"邮件发送成功 {result}")
    print("所有邮件发送完毕")


def slow_task() -> str:
    print("慢任务开始执行...")
    time.sleep(10)
    print("慢任务执行完毕")
    return "success"


def future_test():
    """
    future 的一些基础方法
    """
    with ThreadPoolExecutor(max_workers=2) as executor:
        future = executor.submit(slow_task)
        print(f"任务是否完成: {future.done()}")

        # 尝试取消任务
        cancel_success = future.cancel()
        print(f"任务是否取消成功: {cancel_success}")

        # 超时等待
        try:
            result = future.result(timeout=5)
            print(f"任务执行结果: {result}")
        except TimeoutError:
            print("等待任务结果超时")

        # 检查任务执行是否异常
        try:
            ex = future.exception(timeout=0)
            if ex:
                print("任务执行异常")
            else:
                print("任务执行正常")
        except TimeoutError:
            print("检查任务异常超时")

        result = future.result(timeout=10)
        print(f"任务执行结果: {result}")


def risky_task(num: int) -> int:
    if num == 2:
        raise ValueError("num 不能等于 2")
    print(f"任务 {num} 执行成功")
    return num * 2


def thread_pool_four():
    """
    测试线程池，批量提交任务，按完成顺序处理
    """
    nums = [1, 2, 3, 4]
    print(f"待执行的任务列表: {nums}")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(risky_task, num) for num in nums]
        for i, future in enumerate(futures):
            try:
                result = future.result(timeout=5)
                print(f"任务 {i} 执行结果: {result}")
            except ValueError as e:
                print(f"任务 {i} 执行异常: {e}")
            except TimeoutError as t_e:
                print(f"任务 {i} 执行超时: {t_e}")


def call_back(future):
    print(f"任务 {future} 执行完成, 结果: {future.result()}")


def download_url(url: str) -> str:
    print(f"开始下载 {url}")
    time.sleep(2)
    return fake.url()


def thread_pool_five():
    """
    测试线程池，批量提交任务，增加回调函数
    """
    urls = [
        "https://www.baidu.com",
        "https://www.sina.com.cn",
        "https://www.taobao.com",
        "https://www.jd.com",
    ]
    print(f"待下载的URL列表: {urls}")
    with ThreadPoolExecutor(max_workers=2) as executor:
        for url in urls:
            future = executor.submit(download_url, url)
            # 增加回调函数，任务完成后调用
            future.add_done_callback(call_back)


def main():
    # print("=" * 20)
    # print("线程池的基础使用, 提交任务到线程池中执行")
    # thread_pool_one()
    # print("=" * 20)

    """
    map和submit的区别：map按提交顺序返回结果，submit可以用as_completed按完成顺序处理。
    """
    # print("线程池的批量提交任务")
    # thread_pool_two()
    # print("=" * 20)

    # print("线程池的 map方法, 严格按照输入的顺序返回结果")
    # thread_pool_three()
    # print("=" * 20)

    # print("future 的一些基础方法")
    # future_test()
    # print("=" * 20)

    # print("线程池的批量提交任务, 增加异常处理逻辑")
    # thread_pool_four()
    # print("=" * 20)

    print("线程池的批量提交任务, 增加回调函数")
    thread_pool_five()
    print("=" * 20)


if __name__ == "__main__":
    main()
