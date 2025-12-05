import time
import uvicorn

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse

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


@app.get("/add/{a}/{b}")
def add(a: int, b: int):
    """
    测试加法操作，抛出异常
    """
    if a == 0 or b == 0:
        raise ValueError("a和b不能为0")

    return {"result": a + b}


@app.exception_handler(ValueError)
def handle_value_error(request, exc):
    print(f"值错误异常处理, request={request}, exc={str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"message": "Bad request"},
    )


# 全局异常处理
@app.exception_handler(Exception)
def handle_exception(request, exc):
    print(f"全局异常处理, request={request}, exc={str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


def run_background_task(name: str):
    print(f"后台任务开始运行，name={name}")
    time.sleep(5)
    print(f"后台任务运行完成，name={name}")


if __name__ == "__main__":
    # reload=True 开启自动重载，开发时使用
    uvicorn.run(app="01_fast_api_demo:app", host="0.0.0.0", port=8000, reload=True, workers=1)
