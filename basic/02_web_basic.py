from fastapi import FastAPI

app = FastAPI(
    title="Simple Agent Chat",
    version="1.0",
    description="A simple agent chat API",
)


@app.get("/")
def say_hello():
    return {"Hello": "World"}


if __name__ == "__main__":
    import uvicorn

    print("FastAPI server is running at http://0.0.0.0:8000")
    print("FastAPI Docs is http://0.0.0.0:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
