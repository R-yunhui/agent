"""
真正的流式输出接口示例
包含多种实用场景的流式响应
"""
import uvicorn
import asyncio
import json
import random
import time
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from typing import Generator, AsyncGenerator

app = FastAPI(title="流式响应示例")


# 0. 简单的流式测试接口
@app.get("/simple-stream")
async def simple_stream():
    """最简单的流式输出测试"""

    async def generate_simple() -> AsyncGenerator[str, None]:
        for i in range(10):
            message = f"第 {i+1} 条消息 - {datetime.now().strftime('%H:%M:%S')}\n"
            yield message
            await asyncio.sleep(1)  # 每秒输出一条

    return StreamingResponse(
        generate_simple(),
        media_type="text/plain; charset=utf-8",
    )


# 1. 模拟聊天机器人流式响应
@app.get("/chat-stream")
async def chat_stream(message: str = Query(..., description="用户消息")):
    """模拟ChatGPT式的流式聊天响应"""

    async def generate_chat_response() -> AsyncGenerator[str, None]:
        # 模拟AI思考和回复过程
        responses = [
            f"收到您的消息：{message}\n",
            "正在思考中...\n",
            "根据您的问题，我认为：\n",
            "首先，这是一个很好的问题。\n",
            "其次，我建议您可以从以下几个方面考虑：\n",
            "1. 分析问题的核心\n",
            "2. 寻找可行的解决方案\n",
            "3. 评估不同方案的优缺点\n",
            "希望这个回答对您有帮助！\n"
        ]

        for response in responses:
            # 模拟打字效果，逐字输出
            for char in response:
                yield f"data: {json.dumps({'content': char, 'type': 'text'})}\n\n"
                await asyncio.sleep(0.05)  # 50ms延迟

            await asyncio.sleep(0.3)  # 句子间停顿

        # 发送结束标记
        yield f"data: {json.dumps({'content': '', 'type': 'end'})}\n\n"

    return StreamingResponse(
        generate_chat_response(),
        media_type="text/plain; charset=utf-8",
    )


# 2. 实时数据流（股价、传感器数据等）
@app.get("/data-stream")
async def real_time_data_stream(data_type: str = Query("stock", description="数据类型: stock, sensor, weather")):
    """实时数据流，模拟股价、传感器数据等"""

    async def generate_real_time_data() -> AsyncGenerator[str, None]:
        count = 0
        base_value = 100.0

        while count < 50:  # 发送50条数据
            timestamp = datetime.now().isoformat()

            if data_type == "stock":
                # 模拟股价波动
                change = random.uniform(-2, 2)
                base_value += change
                data = {
                    "timestamp": timestamp,
                    "symbol": "AAPL",
                    "price": round(base_value, 2),
                    "change": round(change, 2),
                    "volume": random.randint(1000, 10000)
                }
            elif data_type == "sensor":
                # 模拟传感器数据
                data = {
                    "timestamp": timestamp,
                    "temperature": round(random.uniform(20, 35), 1),
                    "humidity": round(random.uniform(40, 80), 1),
                    "pressure": round(random.uniform(1000, 1020), 1)
                }
            else:  # weather
                # 模拟天气数据
                data = {
                    "timestamp": timestamp,
                    "location": "北京",
                    "temperature": random.randint(-5, 35),
                    "weather": random.choice(["晴", "多云", "阴", "小雨", "雪"]),
                    "wind_speed": round(random.uniform(0, 15), 1)
                }

            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.5)  # 每500ms发送一次数据
            count += 1

    return StreamingResponse(
        generate_real_time_data(),
        media_type="text/plain; charset=utf-8",
    )


# 3. 日志流式输出
@app.get("/log-stream")
async def log_stream():
    """模拟实时日志输出"""

    async def generate_logs() -> AsyncGenerator[str, None]:
        log_levels = ["INFO", "DEBUG", "WARNING", "ERROR"]
        services = ["user-service", "order-service", "payment-service", "notification-service"]

        for i in range(30):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            level = random.choice(log_levels)
            service = random.choice(services)

            if level == "ERROR":
                message = f"Database connection failed, retrying..."
            elif level == "WARNING":
                message = f"High memory usage detected: {random.randint(80, 95)}%"
            else:
                message = f"Processing request #{random.randint(1000, 9999)}"

            log_entry = f"[{timestamp}] [{level}] [{service}] {message}\n"
            yield log_entry

            # 错误日志间隔短一些，模拟紧急情况
            delay = 0.2 if level == "ERROR" else random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)

    return StreamingResponse(
        generate_logs(),
        media_type="text/plain; charset=utf-8",
    )


# 4. 大文件分块传输
@app.get("/file-stream")
async def file_stream():
    """模拟大文件分块流式传输"""

    async def generate_file_chunks() -> AsyncGenerator[bytes, None]:
        # 模拟一个大文件，分块传输
        total_chunks = 20
        chunk_size = 1024  # 1KB per chunk

        for i in range(total_chunks):
            # 生成模拟数据
            chunk_data = f"文件块 {i+1}/{total_chunks} - " + "数据" * 200 + "\n"
            chunk_bytes = chunk_data.encode('utf-8')

            # 确保每个块大小一致
            if len(chunk_bytes) < chunk_size:
                chunk_bytes += b'0' * (chunk_size - len(chunk_bytes))

            yield chunk_bytes
            await asyncio.sleep(0.5)  # 模拟网络延迟，使用异步sleep

    return StreamingResponse(
        generate_file_chunks(),
        media_type="application/octet-stream",
    )


# 5. Server-Sent Events (SSE) 格式
@app.get("/sse-stream")
async def sse_stream():
    """标准的Server-Sent Events格式流"""

    async def generate_sse() -> AsyncGenerator[str, None]:
        event_id = 0

        while event_id < 20:
            event_id += 1
            timestamp = datetime.now().isoformat()

            # SSE格式：id, event, data
            sse_data = f"id: {event_id}\n"
            sse_data += f"event: message\n"
            sse_data += f"data: {json.dumps({'id': event_id, 'timestamp': timestamp, 'message': f'这是第{event_id}条SSE消息'}, ensure_ascii=False)}\n\n"

            yield sse_data
            await asyncio.sleep(1)

        # 发送结束事件
        yield f"id: {event_id + 1}\nevent: close\ndata: 流结束\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
    )


# 6. JSON流式输出
@app.get("/json-stream")
async def json_stream():
    """JSON格式的流式输出"""

    async def generate_json_stream() -> AsyncGenerator[str, None]:
        # 开始JSON数组
        yield "[\n"

        for i in range(10):
            data = {
                "id": i + 1,
                "timestamp": datetime.now().isoformat(),
                "value": random.randint(1, 100),
                "status": random.choice(["active", "inactive", "pending"])
            }

            json_str = json.dumps(data, ensure_ascii=False, indent=2)

            if i > 0:
                yield ",\n"
            yield json_str

            await asyncio.sleep(0.5)

        # 结束JSON数组
        yield "\n]"

    return StreamingResponse(
        generate_json_stream(),
        media_type="application/json; charset=utf-8",
    )


if __name__ == "__main__":
    print("🚀 流式响应服务器启动")
    print("📋 可用接口:")
    print("  ⚡ 简单测试: http://localhost:8000/simple-stream")
    print("  💬 聊天流: http://localhost:8000/chat-stream?message=你好")
    print("  📊 数据流: http://localhost:8000/data-stream?data_type=stock")
    print("  📝 日志流: http://localhost:8000/log-stream")
    print("  📁 文件流: http://localhost:8000/file-stream")
    print("  🔄 SSE流: http://localhost:8000/sse-stream")
    print("  📋 JSON流: http://localhost:8000/json-stream")
    print("  📖 API文档: http://localhost:8000/docs")
    print()
    print("💡 测试建议:")
    print("  - 用浏览器访问 /simple-stream 查看最直观的流式效果")
    print("  - 用 curl 命令测试: curl http://localhost:8000/simple-stream")
    print("  - 观察数据是否逐条显示，而不是一次性返回")

    uvicorn.run(app, host="0.0.0.0", port=8000)