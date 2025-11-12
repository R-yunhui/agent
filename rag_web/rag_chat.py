from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import uvicorn
import os
import uuid
import yaml
import asyncio
from datetime import datetime

from rag_web import rag_agent

# 加载配置
config_path = os.path.join(os.path.dirname(__file__), "config/config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 创建上传目录
FILE_DIR_PATH = os.path.join(os.path.dirname(__file__), config["app"]["upload_dir"])
os.makedirs(FILE_DIR_PATH, exist_ok=True)

app = FastAPI(
    title=config["app"]["name"],
    version=config["app"]["version"],
    description="一个支持 RAG 的 AI 对话系统",
)


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话 ID（可选，用于多轮对话）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "你好，请介绍一下自己",
                "session_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


class ChatResponse(BaseModel):
    """聊天响应模型"""
    session_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="AI 回复")


class EmbeddingRequest(BaseModel):
    """Embedding 请求模型"""
    session_id: str = Field(..., description="会话 ID")


class EmbeddingResponse(BaseModel):
    """Embedding 响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="执行结果消息")
    document_count: Optional[int] = Field(None, description="处理的文档数量")


@app.get("/", response_class=HTMLResponse, tags=["页面"])
async def index():
    """返回前端聊天页面"""
    html_path = os.path.join(os.path.dirname(__file__), "chat_ui.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <head>
                <meta charset="utf-8">
                <title>聊天页面未找到</title>
            </head>
            <body>
                <h1>聊天页面未找到</h1>
                <p>请确保 chat_ui.html 文件存在</p>
            </body>
        </html>
        """


@app.post(
    path="/api/chat",
    tags=["聊天"],
    response_model=ChatResponse,
    description="发送消息与 AI 对话（非流式）"
)
async def chat(request: ChatRequest):
    """
    与 AI 进行对话
    :param request: 聊天请求
    :return: AI 的回复
    """
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # 调用 RAG 执行模块
        response_stream = rag_agent.chat_with_memory(request.message, session_id)

        # 收集流式响应
        full_response = ""
        for chunk in response_stream:
            if hasattr(chunk, 'content'):
                full_response += chunk.content

        return ChatResponse(
            session_id=session_id,
            message=full_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败：{str(e)}")


@app.post(
    path="/api/chat/stream",
    tags=["聊天"],
    description="发送消息与 AI 对话（流式响应）"
)
async def chat_stream(request: ChatRequest):
    """
    与 AI 进行流式对话
    :param request: 聊天请求
    :return: 流式响应
    """
    session_id = request.session_id or str(uuid.uuid4())

    async def generate():
        try:
            # 首先发送 session_id
            yield f"data: {{'session_id': '{session_id}', 'type': 'start'}}\n\n"

            # 调用 RAG 执行模块
            response_stream = rag_agent.chat_with_memory(request.message, session_id)

            # 流式返回响应
            for chunk in response_stream:
                if hasattr(chunk, 'content') and chunk.content:
                    # 使用 SSE 格式
                    data = {
                        'content': chunk.content,
                        'type': 'content'
                    }
                    yield f"data: {data}\n\n"
                    await asyncio.sleep(0.01)  # 稍微延迟，模拟打字效果

            # 发送结束信号
            yield f"data: {{'type': 'end'}}\n\n"
        except Exception as e:
            error_data = {
                'type': 'error',
                'message': str(e)
            }
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post(
    path="/api/upload",
    tags=["文件上传"],
    description="上传单个文件"
)
async def upload_file(file: UploadFile = File(...)):
    """
    上传单个文件
    :param file: 要上传的文件
    :return: 上传结果（包含原文件名和保存路径）
    """
    try:
        # 处理文件名（防路径穿越 + 防覆盖）
        filename = os.path.basename(file.filename)  # 去除路径部分，避免../../等恶意路径
        unique_id = uuid.uuid4().hex[:8]  # 生成唯一ID
        safe_filename = f"{unique_id}_{filename}"
        file_path = os.path.join(FILE_DIR_PATH, safe_filename)

        # 分块写入文件（适合大文件，减少内存占用）
        with open(file_path, "wb") as f:
            while contents := await file.read(1024 * 1024):  # 每次读取1MB
                f.write(contents)

        return {
            "original_filename": filename,
            "saved_filename": safe_filename,
            "message": "上传成功"
        }
    except Exception as e:
        # 捕获异常并返回友好错误信息
        raise HTTPException(status_code=500, detail=f"文件上传失败：{str(e)}")


@app.post(
    path="/api/upload/multiple",
    tags=["文件上传"],
    description="上传多个文件"
)
async def upload_files(files: list[UploadFile] = File(...)):
    """
    上传多个文件
    :param files: 要上传的文件列表
    :return: 所有文件的上传结果列表
    """
    results = []
    for file in files:
        try:
            # 调用单文件上传接口处理每个文件，并收集结果
            result = await upload_file(file)
            results.append(result)
        except HTTPException as e:
            # 单个文件失败不影响其他文件，记录错误信息
            results.append({
                "original_filename": os.path.basename(file.filename),
                "message": f"上传失败：{e.detail}"
            })
    return results


@app.post(
    path="/api/embedding",
    tags=["RAG"],
    response_model=EmbeddingResponse,
    description="对上传的文件进行 Embedding 并存储到向量数据库"
)
async def create_embedding(request: EmbeddingRequest):
    """
    对上传的文件进行 Embedding
    :param request: Embedding 请求
    :return: 执行结果
    """
    try:
        # 调用 RAG 执行模块处理文件
        vectorstore = rag_agent.rag_execute_with_file(FILE_DIR_PAT, request.session_id)

        return EmbeddingResponse(
            success=True,
            message="文件 Embedding 完成，已存储到向量数据库",
            document_count=None  # 可以从 vectorstore 获取文档数量
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding 失败：{str(e)}")


@app.get(
    path="/api/health",
    tags=["系统"],
    description="健康检查"
)
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": config["app"]["version"]
    }


@app.get(
    path="/api/config",
    tags=["系统"],
    description="获取系统配置（不含敏感信息）"
)
async def get_config():
    """获取系统配置"""
    return {
        "app_name": config["app"]["name"],
        "version": config["app"]["version"],
        "model": config["llm"]["model"],
        "streaming": config["llm"]["streaming"],
        "welcome_message": config["prompts"]["welcome"]
    }


if __name__ == "__main__":
    print(f"🚀 {config['app']['name']} v{config['app']['version']} 正在启动...")
    print(f"📍 服务地址: http://{config['app']['host']}:{config['app']['port']}")
    print(f"📁 文件上传目录: {FILE_DIR_PATH}")
    print(f"📝 API 文档: http://{config['app']['host']}:{config['app']['port']}/docs")

    uvicorn.run(
        app,
        host=config["app"]["host"],
        port=config["app"]["port"]
    )
