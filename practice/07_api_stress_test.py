"""
VL模型接口压测脚本
- 图片URL转base64
- 并发请求压测
- 统计响应时间、成功率等指标
"""

import asyncio
import base64
import os
from pathlib import Path
import json
import argparse

import time
from dataclasses import dataclass, field
from typing import Any, Optional
from PIL import Image
from io import BytesIO
import re

import aiohttp

# 多模型配置
MODELS_CONFIG = {
    "qwen3-omni-30b": {
        "api_url": "http://192.168.2.54:9015/v1/chat/completions",
        "api_key": "gw-cNG7EqGWyej6JRfwZbngDzkgtliZ0Sxc2UHgYjwd7Ts",
        "model_name": "qwen3-omni-30b",
    },
    "mini_cpm": {
        "api_url": "http://192.168.2.54:9015/v1/chat/completions",
        "api_key": "gw-cNG7EqGWyej6JRfwZbngDzkgtliZ0Sxc2UHgYjwd7Ts",
        "model_name": "mini_cpm",
    },
    "qwen3-vl-32b-instruct": {
        "api_url": "http://192.168.2.59:8000/v1/chat/completions",
        "api_key": "93e5f02e99061db3b6113e8db46a0fbd",
        "model_name": "qwen3-vl-32b-instruct",
    },
}


# 用户提示词模板
USER_PROMPT_TEMPLATE = """
**检测内容：**
{{rule_text}}
"""


@dataclass
class StressTestResult:
    """压测结果统计"""

    model_name: str = ""  # 模型名称
    total_requests: int = 0
    success_count: int = 0
    fail_count: int = 0
    correct_count: int = 0  # 结果符合预期的数量
    response_times: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0
        return self.success_count / self.total_requests * 100

    @property
    def correct_rate(self) -> float:
        """预期符合率"""
        if self.success_count == 0:
            return 0
        return self.correct_count / self.success_count * 100

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
        print(f"请求成功数: {self.success_count}")
        print(f"请求失败数: {self.fail_count}")
        print(f"请求成功率: {self.success_rate:.2f}%")
        print("-" * 30)
        print(f"符合预期数: {self.correct_count}")
        print(f"符合预期率: {self.correct_rate:.2f}% (基于成功请求)")
        print("-" * 30)
        print(f"平均响应时间: {self.avg_response_time:.2f}s")
        print(f"最小响应时间: {self.min_response_time:.2f}s")
        print(f"最大响应时间: {self.max_response_time:.2f}s")
        if self.errors:
            print(f"\n错误信息 (前5条):")
            for err in self.errors[:5]:
                print(f"  - {err}")


def build_request_payload(
    model_name: str,
    positive_examples: list[str],
    negative_examples: list[str],
    target_images: list[str],
    rule_text: str,
) -> dict[str, Any]:
    """
    构建请求体 (Few-Shot 模式)

    Args:
        model_name: 模型名称
        positive_examples: 正例图片列表 (base64)
        negative_examples: 反例图片列表 (base64)
        target_images: 待测图片列表 (base64)
        rule_text: 规则文本
    """

    # 1. 准备标准图片消息片段 (作为正例参考)
    std_img_contents = [
        {"type": "image_url", "image_url": {"url": url}} for url in positive_examples
    ]

    # 2. 准备时序图片消息片段 (作为反例参考)
    seq_img_contents = [
        {"type": "image_url", "image_url": {"url": url}} for url in negative_examples
    ]

    # 3. 准备目标测试图片消息片段
    target_img_contents = []
    # 如果 target_images 也是时序图，需要给个标签，或者直接放图
    # 这里假设如果是时序图，每张图都加进去
    for index, url in enumerate(target_images):
        target_img_contents.append({"type": "text", "text": f"#步骤{index+1}"})
        target_img_contents.append({"type": "image_url", "image_url": {"url": url}})

    # 3. 组装 user 消息内容
    user_content = [
        {
            "type": "text",
            "text": USER_PROMPT_TEMPLATE.replace("{{rule_text}}", rule_text),
        },
        # --- 正例展示 ---
        {
            "type": "text",
            "text": "以下是**正例图片（合格标准）**，体现了符合要求的特征：",
        },
        *std_img_contents,
        # --- 反例展示 ---
        {
            "type": "text",
            "text": "以下是**反例图片（不合格标准）**，体现了不符合要求的特征：",
        },
        *seq_img_contents,
        # --- 实际测试 ---
        {
            "type": "text",
            "text": "请观察下面的**测试图片**，并判断是否符合：",
        },
        *target_img_contents,
    ]

    payload = {
        "model": model_name,
        "enable_thinking": False,
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        你是一个智能视觉质检员。你的任务是根据用户提供的“正例图片（合格）”和“反例图片（不合格）”，学习视觉特征的差异，然后判断“测试图片”属于哪一类。

                        输出规则：
                        1. 仅输出标准的 JSON 格式，不要包含 Markdown 代码块标记（如 ```json）。
                        2. **is_compliant**: 如果测试图符合正例的特征，为 true；如果符合反例的特征或存在缺陷，为 false。
                        3. **reason**: 简要描述视觉依据，**限制在 15 字以内**。必须具体描述看到了什么（例如：“屏幕黑屏无显示”或“指示灯为绿色”），禁止废话。

                        输出 JSON 模版：
                        {
                            "is_compliant": true,
                            "reason": "屏幕已点亮并显示主界面。",
                            "confidence": "high"
                        }
                        """,
                    }
                ],
            },
            {"role": "user", "content": user_content},
        ],
    }

    return payload


# 支持的图片扩展名
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def load_images_with_names(image_dir: Path) -> list[tuple[str, str]]:
    """
    加载目录下的图片，返回 (文件名, Base64编码) 的列表
    """
    if not image_dir.exists():
        print(f"  ⚠ 目录不存在: {image_dir}")
        return []

    res = []
    # 按文件名排序
    for file_path in sorted(image_dir.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
            with open(file_path, "rb") as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # 获取原始尺寸
                width, height = img.size
                # 计算缩放比例
                scale = min(max_size / width, max_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)

                # 缩放图像
                img_resized = img.resize(
                    (new_width, new_height), Image.Resampling.LANCZOS
                )

                # 保存到内存
                buffer = BytesIO()
                img_resized.save(buffer, format="JPEG", quality=85, optimize=True)
                buffer.seek(0)

                # 转为 base64
                img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

                mime_type = (
                    "image/jpeg"
                    if file_path.suffix.lower() in {".jpg", ".jpeg"}
                    else f"image/{file_path.suffix[1:].lower()}"
                )
                res.append((file_path.name, f"data:{mime_type};base64,{img_base64}"))
    return res


def image_to_base64(image_dir: Path) -> list[str]:
    """保持兼容旧代码的辅助函数，只返回base64列表"""
    return [img[1] for img in load_images_with_names(image_dir)]


async def send_request(
    session: aiohttp.ClientSession,
    payload: dict,
    semaphore: asyncio.Semaphore,
    request_id: int,
    api_url: str,
    api_key: str,
) -> tuple[bool, float, str, Optional[bool]]:
    """发送单个请求"""
    async with semaphore:
        # print(f"  Start: {request_id}")  # 调试：查看并发开始
        start_time = time.time()
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            async with session.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                response_text = await resp.text()
                elapsed = time.time() - start_time

                if resp.status == 200:
                    response_dict = json.loads(response_text)
                    content = response_dict["choices"][0]["message"]["content"]

                    # 尝试提取 JSON 内容
                    model_is_compliant = None
                    reason = "无原因"
                    try:
                        # 移除可能的 markdown 代码块标记
                        clean_content = (
                            content.replace("```json", "").replace("```", "").strip()
                        )
                        res_json = json.loads(clean_content)
                        model_is_compliant = res_json.get("is_compliant")
                        reason = res_json.get("reason", "无原因")
                    except Exception:
                        pass  # 静默失败

                    # 简化日志: 打印关键结果
                    status_icon = (
                        "✅" if model_is_compliant else "❌"
                    )  # 仅代表 compliant 状态, 不代表是否符合预期(因为预期在外面比对)
                    # 如果 model_is_compliant 是 None，说明解析失败
                    if model_is_compliant is None:
                        status_icon = "❓"

                    print(
                        f"  [{request_id}] {status_icon} IsCompliant: {model_is_compliant} | Time: {elapsed:.2f}s | Reason: {reason}"
                    )
                    return True, elapsed, content, model_is_compliant
                else:
                    error_msg = f"状态码: {resp.status}"
                    print(f"  [{request_id}] ❌ 请求失败: {error_msg}")
                    return False, elapsed, error_msg, None

        except asyncio.TimeoutError:
            print(f"  [{request_id}] ⏰ 超时")
            return False, time.time() - start_time, "请求超时", None
        except Exception as e:
            print(f"  [{request_id}] 💥 异常: {e}")
            return False, time.time() - start_time, str(e), None


async def stress_test_single_image(
    payload: dict,
    api_url: str,
    api_key: str,
    model_name: str,
    image_name: str,
    total_requests: int = 10,
    concurrency: int = 5,
    expected_compliant: Optional[bool] = None,
) -> StressTestResult:
    """对单张图片执行压测"""

    result = StressTestResult(model_name=model_name)
    semaphore = asyncio.Semaphore(concurrency)
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [
            send_request(session, payload, semaphore, i + 1, api_url, api_key)
            for i in range(total_requests)
        ]
        responses = await asyncio.gather(*tasks)

    print()  # 换行

    total_time = time.time() - start_time

    last_response_content = ""

    for success, elapsed, content_or_error, model_is_compliant in responses:
        result.total_requests += 1
        result.response_times.append(elapsed)
        if success:
            result.success_count += 1
            last_response_content = content_or_error  # 记录最后一次响应内容用于展示
            # 结果比对
            if expected_compliant is not None and model_is_compliant is not None:
                if model_is_compliant == expected_compliant:
                    result.correct_count += 1
        else:
            result.fail_count += 1
            if content_or_error:
                result.errors.append(content_or_error)

    # 打印单张图片的简要结果
    print(
        f"  [图片: {image_name}] 准确率: {result.correct_rate:.1f}% ({result.correct_count}/{result.success_count}) | 耗时: {total_time:.2f}s"
    )
    # if last_response_content:
    #     print(f"  ▸ 示例输出: {last_response_content[:100]}..." if len(last_response_content) > 100 else f"  ▸ 示例输出: {last_response_content}")

    return result


async def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="VL模型接口压测脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 测试单个案例
  python 07_api_stress_test.py --case 空调运行是否正常

  # 指定基础目录和模型
  python 07_api_stress_test.py --base-dir D:/模型测试 --case 空调运行是否正常 --model mini_cpm

  # 并发压测
  python 07_api_stress_test.py --case 空调运行是否正常 --total-requests 10 --concurrency 5
        """,
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        choices=MODELS_CONFIG.keys(),
        help=f"指定要使用的模型 (可选). 如果不指定，则测试所有模型: {list(MODELS_CONFIG.keys())}",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=r"C:\Users\Admin\Desktop\模型测试",
        help="测试数据的基础目录，包含 positive_examples 和 counter_example 子目录",
    )
    parser.add_argument(
        "--case",
        type=str,
        required=True,
        help="测试案例名称，如: 空调运行是否正常",
    )
    parser.add_argument(
        "--expected-compliant",
        type=str,
        required=True,
        choices=["true", "false"],
        help="【比对项】预期结果是否合规 (true/false)，用于统计符合预期率",
    )
    parser.add_argument(
        "--test-size",
        type=int,
        default=10,
        help="测试源图片数量限制",
    )
    parser.add_argument(
        "--total-requests",
        type=int,
        default=10,
        help="单张图片请求次数 (用于测试稳定性)",
    )
    parser.add_argument("--concurrency", type=int, default=3, help="并发数")
    args = parser.parse_args()

    # 处理 expected_compliant 参数
    expected_compliant = None
    if args.expected_compliant:
        expected_compliant = args.expected_compliant.lower() == "true"

    # 确定要测试的模型列表
    if args.model:
        target_models = [args.model]
    else:
        target_models = list(MODELS_CONFIG.keys())

    # 构建目录路径
    base_dir = Path(args.base_dir)
    print(f"args.expected_compliant: {args.expected_compliant}")
    dir = (
        "positive_examples" if args.expected_compliant == "true" else "counter_example"
    )
    positive_dir = base_dir / "positive_examples" / args.case
    counter_dir = base_dir / "counter_example" / args.case
    test_source_dir = base_dir / "test_example" / args.case / dir

    print(f"测试案例: {args.case}")
    print(f"测试源目录: {test_source_dir}")
    print(f"测试数量: {args.test_size}")

    # 加载 Context 图片
    positive_images = image_to_base64(positive_dir)
    negative_images = image_to_base64(counter_dir)
    print(
        f"加载 Context: 正例 {len(positive_images)} 张, 反例 {len(negative_images)} 张"
    )

    # 加载测试源图片
    test_images_with_name = load_images_with_names(test_source_dir)
    if not test_images_with_name:
        print("❌ 测试源目录下没有找到图片")
        return

    # 截取指定数量
    test_images_with_name = test_images_with_name[: args.test_size]
    print(
        f"计划测试 {len(test_images_with_name)} 张图片, 每张重复请求 {args.total_requests} 次"
    )

    # 读取规则文件
    rule_file = positive_dir / "rule.txt"
    rule_text = "最终结束时，设备的状态必须符合预期的运行状态。"
    if rule_file.exists():
        rule_text = rule_file.read_text(encoding="utf-8").strip()

    # 结果集合
    all_model_stats = []

    # 循环测试每个模型
    for model_key in target_models:
        model_config = MODELS_CONFIG[model_key]
        api_url = model_config["api_url"]
        api_key = model_config["api_key"]
        model_real_name = model_config["model_name"]

        print(f"\n" + "=" * 60)
        print(f"🤖 正在测试模型: {model_key}")
        print("=" * 60)

        # 该模型的整体统计
        total_correct = 0
        total_success_reqs = 0
        total_reqs = 0
        image_stats_list = []

        # 逐张图片测试
        for img_name, img_base64 in test_images_with_name:
            print(f"\n📸 测试图片: {img_name}")
            # 构建 payload
            try:
                payload = build_request_payload(
                    model_name=model_real_name,
                    positive_examples=positive_images,
                    negative_examples=negative_images,
                    target_images=[img_base64],  # 只有这一张图作为 target
                    rule_text=rule_text,
                )
            except Exception as e:
                print(f"❌ 构建请求体错误: {e}")
                continue

            # 执行单张图片压测
            result = await stress_test_single_image(
                payload=payload,
                api_url=api_url,
                api_key=api_key,
                model_name=model_key,
                image_name=img_name,
                total_requests=args.total_requests,
                concurrency=args.concurrency,
                expected_compliant=expected_compliant,
            )

            total_correct += result.correct_count
            total_success_reqs += result.success_count
            total_reqs += result.total_requests

            image_stats_list.append(
                {
                    "name": img_name,
                    "correct": result.correct_count,
                    "total": result.success_count,  # 使用成功请求数计算分母
                    "rate": result.correct_rate,
                    "avg_time": result.avg_response_time,
                    "max_time": result.max_response_time,
                    "min_time": result.min_response_time,
                }
            )
        # 统计该模型整体准确率
        model_accuracy = (
            (total_correct / total_success_reqs * 100) if total_success_reqs > 0 else 0
        )
        print(f"\n📊 模型 [{model_key}] 整体测试结果:")
        print(f"  - 图片数量: {len(test_images_with_name)}")
        print(f"  - 总请求数: {total_reqs}")
        print(f"  - 综合准确率: {model_accuracy:.2f}%")

        all_model_stats.append(
            {
                "model": model_key,
                "accuracy": model_accuracy,
                "total_reqs": total_reqs,
                "image_stats": image_stats_list,
            }
        )

    # 最终汇总
    print("\n")
    print("🏆 最终汇总报告")
    print("=" * 80)

    for stat in all_model_stats:
        print(f"\n🔹 模型: {stat['model']} (综合准确率: {stat['accuracy']:.1f}%)")
        print(
            f"{'图片名称':<40} | {'准确率':<8} | {'通过/总数':<10} | {'平均耗时':<8} | {'最慢耗时':<8} | {'最快耗时':<8}"
        )
        print("-" * 100)
        for img_stat in stat["image_stats"]:
            print(
                f"{img_stat['name']:<40} | {img_stat['rate']:.1f}%     | {img_stat['correct']}/{img_stat['total']:<6} | {img_stat['avg_time']:.2f}s     | {img_stat['max_time']:.2f}s     | {img_stat['min_time']:.2f}s"
            )


if __name__ == "__main__":
    asyncio.run(main())
