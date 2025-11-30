"""
用户数据库模型

定义了用户表的结构，用于存储用户基本信息。
"""

from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.schemas.base import Base


class User(Base):
    """用户表模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(
        String(50), unique=True, nullable=False, index=True, comment="用户名"
    )
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    full_name = Column(String(100), nullable=True, comment="姓名")
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
