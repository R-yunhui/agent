"""
FastAPI 应用主入口

工作报告系统的主应用，负责：
1. 创建 FastAPI 应用实例
2. 注册所有路由
3. 配置 CORS
4. 提供健康检查端点
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from work_record_project.app.api.router import api_router
import os
import logging

# 配置全局日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建 FastAPI 应用
app = FastAPI(
    title="工作报告系统",
    description="基于大模型的日报周报生成系统",
    version="1.0.0",
    docs_url="/docs",      # Swagger 文档地址
    redoc_url="/redoc"     # ReDoc 文档地址
)

# 配置 CORS（允许跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有 API 路由
app.include_router(api_router)

# 挂载静态文件（JS/CSS）
# 注意：必须在注册 API 路由之后，但在根路由之前（虽然顺序不严格影响，但逻辑上清晰）
# 获取 web 目录的绝对路径
web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
app.mount("/static", StaticFiles(directory=web_dir), name="static")


@app.get("/", tags=["页面"])
async def root():
    """
    返回前端主页
    """
    return FileResponse(os.path.join(web_dir, "index.html"))


@app.get("/health", tags=["系统"])
async def health_check():
    """
    健康检查端点
    """
    return {
        "status": "ok",
        "message": "系统运行正常"
    }
