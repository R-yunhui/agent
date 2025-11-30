"""
应用启动脚本

使用 uvicorn 启动 FastAPI 应用
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式，代码修改自动重载
        log_level="info"
    )
