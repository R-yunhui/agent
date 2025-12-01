import asyncio
import json
import logging
import uuid

from typing import Generator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from work_record_project.app.models import ChatRequest, WorkRecordResponse
from work_record_project.app.service import chat_with_llm

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["聊天"])


@router.post("/", description="发送消息与 AI 对话（流式响应）")
async def chat(chat_request: ChatRequest) -> StreamingResponse:
    session_id = chat_request.session_id or str(uuid.uuid4())

    async def generate() -> Generator[str, None, None]:
        try:
            # 开始信号
            yield f"data: {json.dumps({'session_id': session_id, 'type': 'start'})}\n"

            response = chat_with_llm(chat_request.question, session_id)

            for chunk in response:
                if hasattr(chunk, 'content') and chunk.content:
                    data = {'content': chunk.content, 'type': 'content'}
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n"
                    await asyncio.sleep(0.01)

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
