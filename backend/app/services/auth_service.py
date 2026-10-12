from datetime import datetime, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import TokenType
from app.core.redis import (
    is_login_blocked,
    is_token_revoked,
    register_login_failure,
    reset_login_failures,
    set_token_revoked,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.audit_service import audit


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    email = email.strip().lower()

    user = await db.scalar(select(User).where(User.email == email))

    if not user:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


async def login(
    db: AsyncSession,
    request: Request,
    email: str,
    password: str,
) -> TokenResponse:
    email = email.strip().lower()

    if await is_login_blocked(email):
        await audit(
            db,
            action="auth.login_blocked",
            resource="user",
            request=request,
            detail={"email": email},
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Intente más tarde.",
        )

    user = await authenticate_user(db, email, password)

    if not user:
        await register_login_failure(email)

        await audit(
            db,
            action="auth.login_failed",
            resource="user",
            request=request,
            detail={"email": email},
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    await reset_login_failures(email)

    access_token, _ = create_access_token(str(user.id), user.role.value)
    refresh_token, _ = create_refresh_token(str(user.id), user.role.value)

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    await audit(
        db,
        action="auth.login",
        resource="user",
        resource_id=user.id,
        user_id=user.id,
        request=request,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_tokens(
    db: AsyncSession,
    request: Request,
    refresh_token: str,
) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
        )

    if payload.get("type") != TokenType.REFRESH.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token proporcionado no es un refresh token",
        )

    jti = payload.get("jti")

    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    if await is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocado",
        )

    try:
        user_id = UUID(payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    user = await db.get(User, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no válido",
        )

    now = int(datetime.now(timezone.utc).timestamp())
    ttl = int(payload["exp"] - now)

    await set_token_revoked(jti, ttl)

    access_token, _ = create_access_token(str(user.id), user.role.value)
    new_refresh_token, _ = create_refresh_token(str(user.id), user.role.value)

    await audit(
        db,
        action="auth.refresh",
        resource="user",
        resource_id=user.id,
        user_id=user.id,
        request=request,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def logout(
    db: AsyncSession,
    request: Request,
    access_token: str,
    refresh_token: str | None,
    current_user: User,
) -> None:
    try:
        payload = decode_token(access_token)
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = int(payload.get("exp", now) - now)

        jti = payload.get("jti")

        if jti:
            await set_token_revoked(jti, ttl)

    except jwt.PyJWTError:
        pass

    if refresh_token:
        try:
            refresh_payload = decode_token(refresh_token)

            if (
                refresh_payload.get("type") == TokenType.REFRESH.value
                and refresh_payload.get("sub") == str(current_user.id)
            ):
                now = int(datetime.now(timezone.utc).timestamp())
                ttl = int(refresh_payload.get("exp", now) - now)
                refresh_jti = refresh_payload.get("jti")

                if refresh_jti:
                    await set_token_revoked(refresh_jti, ttl)

        except jwt.PyJWTError:
            pass

    await audit(
        db,
        action="auth.logout",
        resource="user",
        resource_id=current_user.id,
        user_id=current_user.id,
        request=request,
    )
