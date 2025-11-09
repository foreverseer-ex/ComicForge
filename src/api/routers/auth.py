from __future__ import annotations

from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from pydantic import BaseModel, Field
from fastapi import Body
from sqlmodel import select

from api.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    token_hash,
    get_current_user_claims,
    require_roles,
)
from api.services.db import DatabaseSession
from api.schemas.user import User, RefreshToken


class UserPublic(BaseModel):
    id: UUID
    username: str
    aliases: Optional[List[str]] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

router = APIRouter(prefix="/auth", tags=["认证与授权"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    role: Optional[str] = Field(default="viewer")
    aliases: Optional[List[str]] = None


class LoginRequest(BaseModel):
    username: str
    password: str


REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth/refresh"


@router.post("/register")
def register(
    username: str = Body(...),
    password: str = Body(...),
    role: Optional[str] = Body("viewer"),
    aliases: Optional[List[str]] = Body(None),
):
    with DatabaseSession() as db:
        exists = db.exec(select(User).where(User.username == username)).first()
        if exists is not None:
            raise HTTPException(status_code=400, detail="用户名已存在")
        user = User(
            username=username,
            aliases=aliases,
            password_hash=hash_password(password),
            role=role or "viewer",
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.refresh(user)
        return {
            "id": user.id,
            "username": user.username,
            "aliases": user.aliases,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }


@router.post("/login")
def login(
    response: Response,
    username: str = Body(...),
    password: str = Body(...),
):
    with DatabaseSession() as db:
        # username 或 alias 匹配（去除空格）
        input_name = (username or "").strip()
        stmt = select(User).where(User.username == input_name)
        user = db.exec(stmt).first()
        # 若严格匹配失败，尝试大小写不敏感匹配（全表扫描回退）
        if user is None and input_name:
            users_by_name = db.exec(select(User)).all()
            for u in users_by_name:
                if (u.username or "").strip().lower() == input_name.lower():
                    user = u
                    break
        if user is None and input_name:
            # 简单 alias 匹配（JSON 数组包含）
            # SQLite 下 JSON 查询不方便，取出全部再匹配
            users = db.exec(select(User)).all()
            for u in users:
                if u.aliases:
                    aliases_set = {str(a).strip() for a in u.aliases}
                    # 不区分大小写匹配
                    aliases_lower = {a.lower() for a in aliases_set}
                    if (input_name in aliases_set) or (input_name.lower() in aliases_lower):
                        user = u
                        break
        if user is None:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="账户已禁用")

        access = create_access_token(sub=str(user.id), role=user.role)

        # 创建刷新令牌
        now = datetime.now(timezone.utc)
        jti = str(uuid4())
        refresh = create_refresh_token(sub=str(user.id), jti=jti)
        rt = RefreshToken(
            user_id=user.id,
            token_hash=token_hash(refresh),
            jti=jti,
            expires_at=now + timedelta(seconds=int(
                __import__('os').getenv('REFRESH_TOKEN_EXPIRE_SECONDS', '1209600')
            )),
            revoked=False,
        )
        db.add(rt)
        # 设置 HttpOnly Cookie
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh,
            httponly=True,
            secure=False,  # 部署到 HTTPS 时改为 True
            samesite="strict",
            path=REFRESH_COOKIE_PATH,
            max_age=int(__import__('os').getenv('REFRESH_TOKEN_EXPIRE_SECONDS', '1209600')),
        )
        return {"access_token": access, "token_type": "bearer", "expires_in": int(__import__('os').getenv('ACCESS_TOKEN_EXPIRE_SECONDS', '900'))}


@router.post("/refresh")
def refresh(response: Response, request: Request):
    """使用 HttpOnly Cookie 中的刷新令牌换取新的访问令牌"""
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    with DatabaseSession() as db:
        try:
            payload = decode_token(token)
            if payload.get("type") != "refresh":
                raise ValueError("invalid token type")
        except Exception:
            raise HTTPException(status_code=401, detail="刷新令牌无效")
        token_h = token_hash(token)
        rec = db.exec(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_h,
                RefreshToken.revoked == False
            )
        ).first()
        if rec is None or rec.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="刷新令牌失效")
        # 颁发新 access
        user = db.get(User, rec.user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="用户不可用")
        access = create_access_token(sub=str(rec.user_id), role=user.role)
        return {"access_token": access, "token_type": "bearer", "expires_in": int(__import__('os').getenv('ACCESS_TOKEN_EXPIRE_SECONDS', '900'))}


@router.post("/refresh-cookie")
def refresh_cookie(response: Response, request: Request):
    # 兼容：通过 Cookie 刷新
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    with DatabaseSession() as db:
        try:
            payload = decode_token(token)
            if payload.get("type") != "refresh":
                raise ValueError("invalid token type")
        except Exception:
            raise HTTPException(status_code=401, detail="刷新令牌无效")
        token_h = token_hash(token)
        rec = db.exec(select(RefreshToken).where(RefreshToken.token_hash == token_h, RefreshToken.revoked == False)).first()
        if rec is None or rec.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="刷新令牌失效")
        # 颁发新 access
        access = create_access_token(sub=str(rec.user_id), role=db.get(User, rec.user_id).role)
        return {"access_token": access, "token_type": "bearer", "expires_in": int(__import__('os').getenv('ACCESS_TOKEN_EXPIRE_SECONDS', '900'))}


@router.post("/logout")
def logout(response: Response, claims: dict = Depends(get_current_user_claims)):
    """登出：撤销该用户所有刷新令牌，并清除 Cookie"""
    with DatabaseSession() as db:
        tokens = db.exec(select(RefreshToken).where(RefreshToken.user_id == UUID(claims["sub"])) ).all()
        for t in tokens:
            t.revoked = True
        # 提交由 DatabaseSession 上下文完成
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    return {"ok": True}


@router.get("/me")
def me(claims: dict = Depends(get_current_user_claims)):
    with DatabaseSession() as db:
        user = db.get(User, UUID(claims["sub"]))
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {
            "id": user.id,
            "username": user.username,
            "aliases": user.aliases,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
