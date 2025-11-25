"""
Uran FastRTC Server - 主入口文件

这是应用的主入口，负责：
1. 配置日志
2. 创建 FastAPI 应用实例
3. 挂载 WebRTC Stream
4. 注册路由
5. 启动服务器

业务逻辑已拆分到独立模块：
- handlers/webrtc_handler.py: WebRTC 音视频处理逻辑
- routes/frontend.py: 前端页面路由
- routes/api.py: API 路由
- config.py: 配置管理
"""
import logging
from fastapi import FastAPI
from fastrtc import Stream

# 导入业务逻辑模块
from handlers.webrtc_handler import UranEchoHandler
from routes.frontend import router as frontend_router
from routes.api import create_api_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uran_fast_rtc")


# ============================================================================
# FastAPI 应用初始化
# ============================================================================
def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用
    
    Returns:
        配置好的 FastAPI 应用实例
    """
    app = FastAPI(
        title="Uran FastRTC Server",
        description="WebRTC 音视频录制服务",
        version="1.0.0"
    )
    
    # 初始化 WebRTC Stream
    stream = Stream(
        handler=UranEchoHandler(),
        modality="audio-video",
        mode="send-receive",
    )
    
    # 挂载 WebRTC 路由
    stream.mount(app, "/uran-fast-rtc/api")
    
    # 挂载前端路由
    app.include_router(frontend_router)
    
    # 挂载 API 路由（需要传入 stream 实例）
    api_router = create_api_router(stream)
    app.include_router(api_router)
    
    return app


# 创建应用实例
app = create_app()


# ============================================================================
# 主程序入口
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("启动 Uran FastRTC 服务器")
    logger.info(f"前端页面: http://localhost:8000/uran-fast-rtc/test")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
