from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Column, JSON

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    username: str = Field(index=True, unique=True, max_length=64)
    aliases: Optional[List[str]] = Field(sa_column=Column(JSON), default=None)
    password_hash: str
    role: str = Field(default="viewer", max_length=16)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RefreshToken(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(index=True)
    token_hash: str
    jti: str
    expires_at: datetime
    revoked: bool = Field(default=False)
