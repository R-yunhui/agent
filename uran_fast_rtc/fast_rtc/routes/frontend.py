"""
前端路由模块

负责提供前端页面的路由定义。
这是非业务逻辑代码，专注于 Web 服务层。
"""
import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from config import config

router = APIRouter()


@router.get("/uran-fast-rtc/test")
async def serve_frontend():
    """提供前端 HTML 页面"""
    if os.path.exists(config.html_path):
        with open(config.html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    return HTMLResponse(
        content="<h1>未找到前端页面</h1>",
        status_code=404
    )


@router.get("/")
async def root():
    """根路径重定向"""
    return {"message": "Uran FastRTC Server", "frontend": "/uran-fast-rtc/test"}
