import time
import uvicorn

from fastapi import FastAPI, BackgroundTasks

app = FastAPI(
    title="Fast API Demo",
    version="1.0",
    description="这是一个简单的Fast API示例",
)


@app.get("/")
def say_hello(background_tasks: BackgroundTasks):
    # 执行异步任务
    background_tasks.add_task(run_background_task, name="renyh")
    return "Hello, Fast API!"


def run_background_task(name: str):
    print(f"后台任务开始运行，name={name}")
    time.sleep(5)
    print(f"后台任务运行完成，name={name}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
