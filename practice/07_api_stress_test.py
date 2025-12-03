"""
VL模型接口压测脚本
- 图片URL转base64
- 并发请求压测
- 统计响应时间、成功率等指标
"""
import asyncio
import base64
import time
from dataclasses import dataclass, field
from typing import Any

import aiohttp

# 接口配置
API_URL = "http://192.168.2.59:8000/v1/chat/completions"
API_KEY = "93e5f02e99061db3b6113e8db46a0fbd"

# 图片URL列表
IMAGE_URLS = [
    "http://10.10.8.3/storage/files/1991052728714395649.jpg",
    "http://10.10.8.3/storage/files/1991052675736141825.jpg",
    "http://10.10.8.3/storage/files/1991052770305114114.jpg",
    "http://10.10.8.3/storage/files/1991052875385012226.jpg",
    "http://10.10.8.3/storage/files/1991052919467147265.jpg",
    "http://10.10.8.3/storage/files/1991052973317816322.jpg",
    "http://10.10.8.3/storage/files/1991053005089669121.jpg",
    "http://10.10.8.3/storage/files/1991053095791493121.jpg",
    "http://10.10.8.3/storage/files/1991053038832844801.jpg",
    "http://10.10.8.3/storage/files/1990978903469457409.jpg",
    "http://10.10.8.3/storage/files/1991053157204492290.jpg",
    "http://10.10.8.3/storage/files/1991053130218340353.jpg",
]


@dataclass
class StressTestResult:
    """压测结果统计"""
    total_requests: int = 0
    success_count: int = 0
    fail_count: int = 0
    response_times: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0
        return self.success_count / self.total_requests * 100

    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0
        return sum(self.response_times) / len(self.response_times)

    @property
    def min_response_time(self) -> float:
        if not self.response_times:
            return 0
        return min(self.response_times)

    @property
    def max_response_time(self) -> float:
        if not self.response_times:
            return 0
        return max(self.response_times)

    def print_summary(self):
        print("\n" + "=" * 50)
        print("压测结果统计")
        print("=" * 50)
        print(f"总请求数: {self.total_requests}")
        print(f"成功数: {self.success_count}")
        print(f"失败数: {self.fail_count}")
        print(f"成功率: {self.success_rate:.2f}%")
        print(f"平均响应时间: {self.avg_response_time:.2f}s")
        print(f"最小响应时间: {self.min_response_time:.2f}s")
        print(f"最大响应时间: {self.max_response_time:.2f}s")
        if self.errors:
            print(f"\n错误信息 (前5条):")
            for err in self.errors[:5]:
                print(f"  - {err}")


async def download_image_as_base64(session: aiohttp.ClientSession, url: str) -> str:
    """下载图片并转为base64"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                image_data = await resp.read()
                base64_str = base64.b64encode(image_data).decode("utf-8")
                # 根据URL扩展名获取图片类型
                return f"data:image/jpeg;base64,{base64_str}"
            else:
                print(f"下载图片失败: {url}, 状态码: {resp.status}")
                return ""
    except Exception as e:
        print(f"下载图片异常: {url}, 错误: {e}")
        return ""


async def download_all_images(image_urls: list[str]) -> dict[str, str]:
    """并发下载所有图片并转为base64"""
    print(f"开始下载 {len(image_urls)} 张图片...")
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [download_image_as_base64(session, url) for url in image_urls]
        results = await asyncio.gather(*tasks)

    image_base64_map = {}
    for url, base64_str in zip(image_urls, results):
        if base64_str:
            image_base64_map[url] = base64_str
            print(f"  ✓ {url.split('/')[-1]}")
        else:
            print(f"  ✗ {url.split('/')[-1]} 下载失败")

    print(f"图片下载完成，耗时: {time.time() - start_time:.2f}s")
    print(f"成功: {len(image_base64_map)}/{len(image_urls)}")
    return image_base64_map


def build_request_payload(image_base64_map: dict[str, str]) -> dict[str, Any]:
    """构建请求体"""
    # 标准图片URLs
    standard_image_urls = [
        "http://10.10.8.3/storage/files/1991052728714395649.jpg",
        "http://10.10.8.3/storage/files/1991052675736141825.jpg",
        "http://10.10.8.3/storage/files/1991052770305114114.jpg",
        "http://10.10.8.3/storage/files/1991052875385012226.jpg",
        "http://10.10.8.3/storage/files/1991052919467147265.jpg",
        "http://10.10.8.3/storage/files/1991052973317816322.jpg",
    ]

    # 时序图片URLs (按顺序)
    sequence_images = [
        ("时序图片 #1", "http://10.10.8.3/storage/files/1991053005089669121.jpg"),
        ("时序图片 #2", "http://10.10.8.3/storage/files/1991053038832844801.jpg"),
        ("时序图片 #3", "http://10.10.8.3/storage/files/1991053095791493121.jpg"),
        ("时序图片 #4", "http://10.10.8.3/storage/files/1990978903469457409.jpg"),
        ("时序图片 #5", "http://10.10.8.3/storage/files/1991053130218340353.jpg"),
        ("时序图片 #6", "http://10.10.8.3/storage/files/1991053157204492290.jpg"),
    ]

    # 构建user消息内容
    user_content = [
        {
            "type": "text",
            "text": "一、文字规范如下：\n1. ...\n2. ...\n（这里写你的规范条目）"
        },
        {
            "type": "text",
            "text": "二、以下是若干张标准示例图片，请学习它们体现的规范："
        }
    ]

    # 添加标准图片 (base64格式)
    for url in standard_image_urls:
        if url in image_base64_map:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_base64_map[url]
                }
            })

    user_content.append({
        "type": "text",
        "text": "三、下面是需要审查的时序图片，该图片序列为调整过程，请总体判断是否符合规范，请注意最终勺子的摆放位置是否相同："
    })

    # 添加时序图片 (base64格式)
    for label, url in sequence_images:
        user_content.append({
            "type": "text",
            "text": label
        })
        if url in image_base64_map:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_base64_map[url]
                }
            })

    user_content.append({
        "type": "text",
        "text": "直接回答0或者1,不要多余的文字或json结构，1为通过，0为不通过"
    })

    payload = {
        "model": "qwen3-vl-32b-instruct",
        "enable_thinking": False,
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "你是一个图像规范审查助手，根据给定的“规范说明”和“标准图片”，判断时序图片是否符合规范，并以JSON格式输出结论。"
                    }
                ]
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
    }

    return payload


async def send_request(
        session: aiohttp.ClientSession,
        payload: dict,
        semaphore: asyncio.Semaphore,
        request_id: int
) -> tuple[bool, float, str]:
    """发送单个请求"""
    async with semaphore:
        start_time = time.time()
        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            async with session.post(
                    API_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                elapsed = time.time() - start_time
                response_text = await resp.text()

                if resp.status == 200:
                    print(f"[{request_id}] 成功 - 耗时: {elapsed:.2f}s - 响应: {response_text[:100]}...")
                    return True, elapsed, ""
                else:
                    error_msg = f"状态码: {resp.status}, 响应: {response_text[:200]}"
                    print(f"[{request_id}] 失败 - 耗时: {elapsed:.2f}s - {error_msg}")
                    return False, elapsed, error_msg

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            error_msg = "请求超时"
            print(f"[{request_id}] 超时 - 耗时: {elapsed:.2f}s")
            return False, elapsed, error_msg
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            print(f"[{request_id}] 异常 - 耗时: {elapsed:.2f}s - {error_msg}")
            return False, elapsed, error_msg


async def stress_test(
        payload: dict,
        total_requests: int = 10,
        concurrency: int = 5
) -> StressTestResult:
    """执行压测"""
    print(f"\n开始压测: 总请求数={total_requests}, 并发数={concurrency}")
    print("=" * 50)

    result = StressTestResult()
    semaphore = asyncio.Semaphore(concurrency)

    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [
            send_request(session, payload, semaphore, i + 1)
            for i in range(total_requests)
        ]
        responses = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    for success, elapsed, error in responses:
        result.total_requests += 1
        result.response_times.append(elapsed)
        if success:
            result.success_count += 1
        else:
            result.fail_count += 1
            if error:
                result.errors.append(error)

    print(f"\n压测完成，总耗时: {total_time:.2f}s")
    print(f"QPS: {total_requests / total_time:.2f}")

    return result


async def main():
    # 1. 下载所有图片并转为base64
    image_base64_map = await download_all_images(IMAGE_URLS)

    if not image_base64_map:
        print("没有成功下载任何图片，退出")
        return

    # 2. 构建请求体
    payload = build_request_payload(image_base64_map)
    print(f"\n请求体构建完成，消息内容项数: {len(payload['messages'][1]['content'])}")

    # 3. 执行压测
    # 可以调整参数: total_requests=总请求数, concurrency=并发数
    result = await stress_test(
        payload=payload,
        total_requests=10,  # 总共发送10个请求
        concurrency=5  # 最大并发数为3
    )

    # 4. 打印统计结果
    result.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
