"""
模型测试 - 图片描述（langchain版本）
- 支持原图/质量压缩/分辨率压缩对比测试
- 统计token消耗和耗时
"""
import argparse
import asyncio
import base64
import time
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from enum import Enum

from PIL import Image
from langchain_core.messages import HumanMessage
from langchain_openai.chat_models import ChatOpenAI

# 模型配置
MODELS_CONFIG = {
    "qwen3-vl-32b-instruct": {
        "base_url": "http://192.168.2.54:9015/v1",
        "api_key": "gw-cNG7EqGWyej6JRfwZbngDzkgtliZ0Sxc2UHgYjwd7Ts",
        "model_name": "qwen3-vl-32b-instruct",
    },
    "qwen3-omni-30b": {
        "base_url": "http://192.168.2.54:9015/v1",
        "api_key": "gw-cNG7EqGWyej6JRfwZbngDzkgtliZ0Sxc2UHgYjwd7Ts",
        "model_name": "qwen3-omni-30b",
    },
    "mini_cpm": {
        "base_url": "http://192.168.2.54:9015/v1",
        "api_key": "gw-cNG7EqGWyej6JRfwZbngDzkgtliZ0Sxc2UHgYjwd7Ts",
        "model_name": "mini_cpm",
    },
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
QUALITY_TEST_VALUES = [55]
RESOLUTION_TEST_VALUES = [768]


class TestType(Enum):
    ORIGINAL = "original"
    QUALITY = "quality"
    RESOLUTION = "resolution"


@dataclass
class TestResult:
    test_type: TestType = TestType.ORIGINAL
    config_value: int = 0
    total_requests: int = 0
    success_count: int = 0
    response_times: list = field(default_factory=list)
    prompt_tokens: list = field(default_factory=list)
    completion_tokens: list = field(default_factory=list)
    total_tokens: list = field(default_factory=list)
    image_sizes: list = field(default_factory=list)
    image_dimensions: list = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.test_type == TestType.ORIGINAL:
            return "原图"
        elif self.test_type == TestType.QUALITY:
            return f"质量_{self.config_value}"
        return f"分辨率_{self.config_value}"

    @property
    def success_rate(self) -> float:
        return (self.success_count / self.total_requests * 100) if self.total_requests else 0

    @property
    def avg_response_time(self) -> float:
        return (sum(self.response_times) / len(self.response_times)) if self.response_times else 0

    @property
    def avg_total_tokens(self) -> float:
        return (sum(self.total_tokens) / len(self.total_tokens)) if self.total_tokens else 0

    @property
    def total_image_size_kb(self) -> float:
        return sum(self.image_sizes) / 1024 if self.image_sizes else 0

    @property
    def avg_dimension(self) -> str:
        if not self.image_dimensions:
            return "-"
        avg_w = sum(d[0] for d in self.image_dimensions) / len(self.image_dimensions)
        avg_h = sum(d[1] for d in self.image_dimensions) / len(self.image_dimensions)
        return f"{avg_w:.0f}x{avg_h:.0f}"


def process_image(image_path: Path, test_type: TestType, value: int = 0, save_dir: Path = None):
    """处理图片"""
    with Image.open(image_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        width, height = img.size

        if test_type == TestType.ORIGINAL:
            quality, final_size = 100, (width, height)
        elif test_type == TestType.QUALITY:
            quality, final_size = value, (width, height)
        else:
            quality, max_size = 85, value
            if width > max_size or height > max_size:
                scale = min(max_size / width, max_size / height)
                new_w, new_h = int(width * scale), int(height * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                final_size = (new_w, new_h)
            else:
                final_size = (width, height)

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)
        image_bytes = buffer.read()

        if save_dir:
            save_dir.mkdir(parents=True, exist_ok=True)
            suffix = "original" if test_type == TestType.ORIGINAL else f"{test_type.value}_{value}"
            with open(save_dir / f"{image_path.stem}_{suffix}.jpg", "wb") as f:
                f.write(image_bytes)

        img_base64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{img_base64}", len(image_bytes), final_size


def get_image_files(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        return []
    return [f for f in sorted(image_dir.iterdir()) if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]


async def call_model(chat_model, image_urls, total_size, image_dims, prompt, semaphore, req_id):
    """调用大模型"""
    async with semaphore:
        start = time.time()
        try:
            content = [{"type": "text", "text": prompt}]
            content.extend({"type": "image_url", "image_url": {"url": url}} for url in image_urls)
            response = await chat_model.ainvoke([HumanMessage(content=content)])
            elapsed = time.time() - start

            usage = response.response_metadata.get("token_usage", {})
            content = response.content
            print(f"大模型调用返回的结果: {content}")
            p, c, t = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), usage.get("total_tokens", 0)
            print(f"  #{req_id:02d} ✓ {elapsed:.2f}s | Token: {p}+{c}={t} | {total_size / 1024:.1f}KB")
            return True, elapsed, p, c, t, total_size, image_dims
        except Exception as e:
            print(f"  #{req_id:02d} ✗ {time.time() - start:.2f}s | 错误: {e}")
            return False, time.time() - start, 0, 0, 0, total_size, image_dims


async def run_test(chat_model, image_files, prompt, test_type, value, total_requests, concurrency, save_dir):
    """执行测试"""
    result = TestResult(test_type=test_type, config_value=value)
    semaphore = asyncio.Semaphore(concurrency)

    labels = {TestType.ORIGINAL: "原图", TestType.QUALITY: f"质量={value}", TestType.RESOLUTION: f"分辨率={value}"}
    print(f"\n[{labels[test_type]}]")

    # 处理图片
    image_urls, image_dims, total_size = [], [], 0
    for path in image_files:
        try:
            url, size, dim = process_image(path, test_type, value, save_dir)
            image_urls.append(url)
            image_dims.append(dim)
            total_size += size
        except Exception as e:
            print(f"  处理失败 {path.name}: {e}")

    if not image_urls:
        return result

    # 并发请求
    tasks = [call_model(chat_model, image_urls, total_size, image_dims, prompt, semaphore, i + 1) for i in
             range(total_requests)]
    for success, elapsed, p, c, t, size, dims in await asyncio.gather(*tasks):
        result.total_requests += 1
        result.response_times.append(elapsed)
        result.image_sizes.append(size)
        result.image_dimensions.extend(dims)
        if success:
            result.success_count += 1
            result.prompt_tokens.append(p)
            result.completion_tokens.append(c)
            result.total_tokens.append(t)

    return result


async def run_comparison_test(image_dir, prompt, model_key, test_mode, total_requests, concurrency):
    """执行对比测试"""
    config = MODELS_CONFIG.get(model_key)
    if not config:
        print(f"未知模型: {model_key}")
        return

    chat_model = ChatOpenAI(base_url=config["base_url"], model=config["model_name"], api_key=config["api_key"],
                            timeout=120)
    image_files = get_image_files(image_dir)
    if not image_files:
        print("没有找到图片")
        return

    # 原图信息
    print(f"\n模型: {model_key} | 图片: {len(image_files)}张 | 模式: {test_mode}")
    for f in image_files:
        with Image.open(f) as img:
            print(f"  {f.name}: {img.size[0]}x{img.size[1]}, {f.stat().st_size / 1024:.1f}KB")

    save_dir = image_dir / "_compressed"
    results = []

    if test_mode in ("original", "all"):
        results.append(
            await run_test(chat_model, image_files, prompt, TestType.ORIGINAL, 0, total_requests, concurrency,
                           save_dir / "original"))

    if test_mode in ("quality", "all"):
        for q in QUALITY_TEST_VALUES:
            results.append(
                await run_test(chat_model, image_files, prompt, TestType.QUALITY, q, total_requests, concurrency,
                               save_dir / "quality"))

    if test_mode in ("resolution", "all"):
        for r in RESOLUTION_TEST_VALUES:
            results.append(
                await run_test(chat_model, image_files, prompt, TestType.RESOLUTION, r, total_requests, concurrency,
                               save_dir / "resolution"))

    # 汇总
    print("\n" + "=" * 80)
    print(f"{'测试类型':<12} | {'成功率':<6} | {'耗时':<8} | {'Token':<8} | {'图片大小':<10} | {'尺寸':<12}")
    print("-" * 80)
    for r in results:
        print(
            f"{r.label:<12} | {r.success_rate:.0f}%    | {r.avg_response_time:.2f}s   | {r.avg_total_tokens:<8.0f} | {r.total_image_size_kb:.1f}KB     | {r.avg_dimension:<12}")
    print("=" * 80)

    # 推荐
    valid = [r for r in results if r.success_rate == 100]
    if len(valid) > 1:
        best_token = min(valid, key=lambda x: x.avg_total_tokens)
        best_speed = min(valid, key=lambda x: x.avg_response_time)
        print(
            f"\n推荐: Token最少={best_token.label}({best_token.avg_total_tokens:.0f}) | 速度最快={best_speed.label}({best_speed.avg_response_time:.2f}s)")


async def main():
    parser = argparse.ArgumentParser(description="VL模型图片压缩对比测试")
    parser.add_argument("--image-dir", type=str, default="C:\\Users\\Admin\\Desktop\\模型测试\\image_test")
    parser.add_argument("--prompt", type=str, default="请用50字分别描述一下下面的图片内容，仅输出中文，不包含其他语言或符号。")
    parser.add_argument("--model", type=str, default="qwen3-omni-30b", choices=MODELS_CONFIG.keys())
    parser.add_argument("--test-mode", type=str, default="all", choices=["original", "quality", "resolution", "all"])
    parser.add_argument("--total-requests", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=3)
    args = parser.parse_args()

    await run_comparison_test(Path(args.image_dir), args.prompt, args.model, args.test_mode, args.total_requests,
                              args.concurrency)


if __name__ == "__main__":
    asyncio.run(main())
