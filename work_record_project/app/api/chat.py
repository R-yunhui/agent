"""
聊天 API

流式响应的聊天接口
"""
import json
import logging
import uuid
from typing import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from work_record_project.app.models import ChatRequest
from work_record_project.app.service import chat_with_llm

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["聊天"])


@router.post("/", description="发送消息与 AI 对话（流式响应）")
def chat(chat_request: ChatRequest) -> StreamingResponse:
    """
    流式聊天接口
    
    使用同步路由 + 同步生成器，FastAPI 会在线程池中处理，不阻塞事件循环。
    """
    session_id = chat_request.session_id or str(uuid.uuid4())

    def generate() -> Iterator[str]:
        """同步生成器，产生 SSE 格式的数据"""
        try:
            # 开始信号
            yield f"data: {json.dumps({'session_id': session_id, 'type': 'start'})}\n"

            # 调用 LLM（同步阻塞，但在线程池中运行）
            response = chat_with_llm(chat_request.question, session_id)

            for chunk in response:
                if hasattr(chunk, 'content') and chunk.content:
                    data = {'content': chunk.content, 'type': 'content'}
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n"

            # 结束信号
            yield f"data: {json.dumps({'type': 'end'})}\n"
        except Exception as e:
            logger.error(f"聊天接口异常: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
