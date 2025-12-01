from typing import Optional

from pydantic import BaseModel
from pydantic.fields import Field


class ChatRequest(BaseModel):
    question: Optional[str] = Field(None, description="用户问题")
    session_id: Optional[str] = Field(None, description="会话 ID")
