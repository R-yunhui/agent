"""
在 FastAPI 中，任何未在路径中声明的参数都会被自动解释为查询参数。这意味着你无需额外配置，就能通过 URL 的查询字符串传递数据
可以使用 pydantic 模型来定义查询参数的结构，这使得参数校验和文档生成更加方便。
"""
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI()

items = [{"item_name": "Item A"}, {"item_name": "Item B"}, {"item_name": "Item C"}]


@app.get("/items/")
async def get_items(skip: int = 0, limit: int = 10):
    return items[skip: skip + limit]


class User(BaseModel):
    username: Optional[str] = Field(..., description="用户名", max_length=11, min_length=1)
    password: Optional[str] = Field(..., description="密码", max_length=11, min_length=8)
    userid: Optional[int] = Field(None, description="用户ID", ge=1, le=11)


users: Dict[int, User] = {}


@app.post("/users")
async def create_user(user: User):
    if user.userid is None:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    users[user.userid] = user
    return user

# 将路径参数 + 查询参数 + 请求体
@app.post("/users/{userid}")
async def get_or_create_user(userid: int, username: str, cur_user: User):
    if userid in users:
        return users[userid]
    else:
        for user_id, user in users.items():
            if user.username == username:
                return users[user_id]
        users[userid] = cur_user
    return cur_user


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
