"""
pyee 实现事件监听
"""
import asyncio
import time
from pyee.asyncio import AsyncIOEventEmitter
from pyee import EventEmitter

async_event_emitter = AsyncIOEventEmitter()

sync_event_emitter = EventEmitter()


# 类似 sync_event_emitter.add_listener('remove_user', user_remove_one)
@sync_event_emitter.on('remove_user')
def user_remove_one(data):
    print(f"[同步1] 开始处理用户删除事件 - {time.strftime('%H:%M:%S')}")
    time.sleep(1)
    print(f"[同步1] 处理完成用户删除事件 - {time.strftime('%H:%M:%S')}")


@sync_event_emitter.on('remove_user')
def user_remove_two(data):
    print(f"[同步2] 开始处理用户删除事件 - {time.strftime('%H:%M:%S')}")
    time.sleep(1)
    print(f"[同步2] 处理完成用户删除事件 - {time.strftime('%H:%M:%S')}")


@async_event_emitter.on("create_user")
async def create_user_one(data):
    print(f"[异步1] 开始处理用户创建事件 - {time.strftime('%H:%M:%S')}")
    await asyncio.sleep(1)
    print(f"[异步1] 处理完成用户创建事件 - {time.strftime('%H:%M:%S')}")


@async_event_emitter.on("create_user")
async def create_user_two(data):
    print(f"[异步2] 开始处理用户创建事件 - {time.strftime('%H:%M:%S')}")
    await asyncio.sleep(1)
    print(f"[异步2] 处理完成用户创建事件 - {time.strftime('%H:%M:%S')}")


class UserService:

    def __init__(self):
        self.users = []

    async def create_user(self, username: str, user_id: int):
        start_time = time.time()
        self.users.append({"username": username, "user_id": user_id})
        async_event_emitter.emit("create_user", self)
        await async_event_emitter.wait_for_complete()
        end_time = time.time()
        print(f"[异步] 所有用户创建事件处理完成，耗时 {end_time - start_time:.2f} 秒")

    def remove_user(self, user_id: int):
        start_time = time.time()
        for i, user in enumerate(self.users):
            if user['user_id'] == user_id:
                del self.users[i]
                print(f"删除用户 {user_id} 成功")
                break
        sync_event_emitter.emit("remove_user", self)
        # 会等待所有同步事件处理完成，才会执行下面的逻辑
        end_time = time.time()
        print(f"[同步] 所有用户删除事件处理完成，耗时 {end_time - start_time:.2f} 秒")


def main():
    user = UserService()
    asyncio.run(user.create_user("张三", 1001))

    print(" = " * 30)

    user.remove_user(1001)


if __name__ == "__main__":
    main()
