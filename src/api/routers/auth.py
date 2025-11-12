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
    claims: dict = Depends(get_current_user_claims),
):
    # 只有管理员可以注册新用户
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以创建用户")
    
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
    from loguru import logger
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
            logger.warning(f"登录失败: 用户不存在 - username={repr(input_name)}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        # 记录收到的密码信息（用于调试，不记录完整密码）
        password_preview = password[:10] + "..." if len(password) > 10 else password
        logger.info(f"登录尝试 - username={repr(input_name)}, password_length={len(password)}, password_preview={repr(password_preview)}")
        
        password_verified = verify_password(password, user.password_hash)
        if not password_verified:
            # 记录配置中的密码长度用于对比
            from api.settings import app_settings
            config_pwd_len = len(app_settings.admin.password) if input_name == app_settings.admin.username else 0
            logger.warning(f"登录失败: 密码错误 - username={repr(input_name)}, received_password_length={len(password)}, config_password_length={config_pwd_len}, user_id={user.id}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        if not user.is_active:
            logger.warning(f"登录失败: 账户已禁用 - username={repr(input_name)}")
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
        if rec is None:
            raise HTTPException(status_code=401, detail="刷新令牌失效")
        # 处理时区问题：如果 expires_at 是 offset-naive，假设它是 UTC
        expires_at = rec.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
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
        if rec is None:
            raise HTTPException(status_code=401, detail="刷新令牌失效")
        # 处理时区问题：如果 expires_at 是 offset-naive，假设它是 UTC
        expires_at = rec.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
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


@router.get("/users")
def list_users(claims: dict = Depends(get_current_user_claims)):
    """获取所有用户列表（仅管理员）"""
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以查看用户列表")
    
    with DatabaseSession() as db:
        users = db.exec(select(User)).all()
        return [
            {
                "id": user.id,
                "username": user.username,
                "aliases": user.aliases,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
            }
            for user in users
        ]


@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    username: Optional[str] = Body(None),
    role: Optional[str] = Body(None),
    is_active: Optional[bool] = Body(None),
    aliases: Optional[List[str]] = Body(None),
    claims: dict = Depends(get_current_user_claims),
):
    """更新用户信息（仅管理员）"""
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以更新用户")
    
    with DatabaseSession() as db:
        user = db.get(User, UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        if username is not None:
            # 检查用户名是否已存在
            existing = db.exec(select(User).where(User.username == username, User.id != user.id)).first()
            if existing:
                raise HTTPException(status_code=400, detail="用户名已存在")
            user.username = username
        
        if role is not None:
            user.role = role
        
        if is_active is not None:
            user.is_active = is_active
        
        if aliases is not None:
            user.aliases = aliases
        
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


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    claims: dict = Depends(get_current_user_claims),
):
    """删除用户（仅管理员）"""
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以删除用户")
    
    with DatabaseSession() as db:
        user = db.get(User, UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 不能删除自己
        if str(user.id) == claims["sub"]:
            raise HTTPException(status_code=400, detail="不能删除自己的账户")
        
        db.delete(user)
        return {"ok": True}


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: str,
    new_password: str = Body(...),
    claims: dict = Depends(get_current_user_claims),
):
    """重置用户密码（仅管理员）"""
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以重置密码")
    
    with DatabaseSession() as db:
        user = db.get(User, UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        user.password_hash = hash_password(new_password)
        db.flush()
        return {"ok": True}
