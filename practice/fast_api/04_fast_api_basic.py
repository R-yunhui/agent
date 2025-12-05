"""
参数校验
如果一个函数的参数中，有默认值的参数在没有默认值的参数前面，Python 会报错。
"""
from fastapi import FastAPI, Query, Path
from typing import Union
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI()


# 查询参数校验
@app.get("/items/")
async def read_items(
        # 校验查询参数 q 为可选的字符串，最大长度为 50，最小长度为 5，描述为 "查询参数", 默认值为 None，支持正则表达式 "^[a-zA-Z0-9_]*$"
        # default=None 不进行设置，说明 q 是必选的  Query(max_length=50, min_length=5, description="查询参数", regex="^[a-zA-Z0-9_]*$")
        # deprecated 标记废弃
        q: Union[str, None] = Query(default=None, max_length=50, min_length=5, description="查询参数",
                                    regex="^[a-zA-Z0-9_]*$"),
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


# 路径参数校验
@app.get("/items/{item_id}")
async def get_items(item_id: int = Path(description="项目 ID", gt=0, lt=1000, example=2)):
    return {"item_id": item_id, "item_name": "电脑项目"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
