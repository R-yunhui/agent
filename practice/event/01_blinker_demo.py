"""
演示 blinker 同步 vs 异步的区别
"""
import asyncio
import time

from blinker import signal

# 定义两个事件
sync_event = signal("sync_event")
async_event = signal("async_event")


# ========== 同步版本 ==========
@sync_event.connect
def sync_handler_1(sender, **kwargs):
    print(f"[同步1] 开始处理 - {time.strftime('%H:%M:%S')}")
    time.sleep(1)  # 模拟耗时操作，会阻塞
    print(f"[同步1] 处理完成 - {time.strftime('%H:%M:%S')}")


@sync_event.connect
def sync_handler_2(sender, **kwargs):
    print(f"[同步2] 开始处理 - {time.strftime('%H:%M:%S')}")
    time.sleep(1)  # 会等上一个完成后才执行
    print(f"[同步2] 处理完成 - {time.strftime('%H:%M:%S')}")


# ========== 异步版本 ==========
@async_event.connect
async def async_handler_1(sender, **kwargs):
    print(f"[异步1] 开始处理 - {time.strftime('%H:%M:%S')}")
    await asyncio.sleep(1)  # 异步等待，不阻塞
    print(f"[异步1] 处理完成 - {time.strftime('%H:%M:%S')}")


@async_event.connect
async def async_handler_2(sender, **kwargs):
    print(f"[异步2] 开始处理 - {time.strftime('%H:%M:%S')}")
    await asyncio.sleep(1)  # 和handler_1几乎同时执行
    print(f"[异步2] 处理完成 - {time.strftime('%H:%M:%S')}")


def test_sync():
    print("=" * 40)
    print("测试同步事件")
    print("=" * 40)
    start = time.time()
    sync_event.send("test")
    print(f"同步总耗时: {time.time() - start:.2f}秒")
    print()


async def test_async():
    print("=" * 40)
    print("测试异步事件")
    print("=" * 40)
    start = time.time()
    await async_event.send_async("test")
    print(f"异步总耗时: {time.time() - start:.2f}秒")


async def test_concurrent():
    print("=" * 40)
    print("测试并发异步事件")
    print("=" * 40)
    start = time.time()
    await send_concurrent(async_event, "test")
    print(f"并发总耗时: {time.time() - start:.2f}秒")


async def send_concurrent(sig, sender, **kwargs):
    """并发执行所有监听器"""
    receivers = sig.receivers_for(sender)
    tasks = []
    for receiver in receivers:
        result = receiver(sender, **kwargs)
        if asyncio.iscoroutine(result):
            tasks.append(result)
    if tasks:
        await asyncio.gather(*tasks)


def main():
    # 先测试同步
    test_sync()

    # 再测试异步
    # blinker 的设计选择——它按顺序 await 每个监听器，而不是用 asyncio.gather 并发执行。
    asyncio.run(test_async())

    # 在并发测试中，异步事件的处理时间是1秒，而同步事件的处理时间是2秒
    # 所以并发测试的总耗时应该是1秒左右，而不是2秒
    asyncio.run(test_concurrent())


if __name__ == "__main__":
    main()
