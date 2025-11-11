from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn
import rag_execute

app = FastAPI(
    title="Simple Rag Web",
    version="1.0",
    description="A simple Rag Web application",
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


class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str
    message_count: int
    last_active: str


@app.get("/", response_class=HTMLResponse, tags=["页面"])
async def index():
    """返回前端聊天页面"""
    html_path = os.path.join(os.getcwd(), "chat_ui.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <body>
                <h1>聊天页面未找到</h1>
                <p>请确保 chat_ui.html 文件存在</p>
            </body>
        </html>
        """


@app.post(
    path="/upload_files",
    tags=["upload_files"],
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
        except Exception as e:
            # 单个文件失败不影响其他文件，记录错误信息
            results.append({
                "original_filename": os.path.basename(file.filename),
                "message": f"上传失败：{e.detail}"
            })
    return results


async def upload_file(file: UploadFile = File(...)) -> dict[str, str]:
    """
    上传单个文件
    :param file: 要上传的文件
    :return: 上传结果（包含原文件名和保存路径）
    """
    try:
        # 处理文件名（防路径穿越 + 防覆盖）
        filename = os.path.basename(file.filename)  # 去除路径部分，避免../../等恶意路径
        unique_id = uuid.uuid4().hex  # 生成唯一ID
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


if __name__ == "__main__":
    print(f"Rag Web Server running")

    uvicorn.run(app, host="0.0.0.0", port=8000)
