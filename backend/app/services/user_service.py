from typing import List
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.audit_service import audit


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    email = email.strip().lower()
    return await db.scalar(select(User).where(User.email == email))


async def create_user(
    db: AsyncSession,
    payload: UserCreate,
    request: Request | None = None,
    actor: User | None = None,
) -> User:
    existing_user = await get_user_by_email(db, payload.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con este correo",
        )

    user = User(
        email=payload.email.strip().lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
        mfa_enabled=False,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    await audit(
        db,
        action="user.created",
        resource="user",
        resource_id=user.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={
            "email": user.email,
            "role": user.role.value,
        },
    )

    return user


async def list_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> List[User]:
    query = (
        select(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return (await db.scalars(query)).all()


async def get_user(
    db: AsyncSession,
    user_id: UUID,
) -> User:
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return user


async def update_user(
    db: AsyncSession,
    user_id: UUID,
    payload: UserUpdate,
    request: Request | None = None,
    actor: User | None = None,
) -> User:
    user = await get_user(db, user_id)

    changes = {}

    if payload.full_name is not None:
        user.full_name = payload.full_name
        changes["full_name"] = payload.full_name

    if payload.role is not None:
        user.role = payload.role
        changes["role"] = payload.role.value

    if payload.is_active is not None:
        user.is_active = payload.is_active
        changes["is_active"] = payload.is_active

    if payload.password is not None:
        user.hashed_password = hash_password(payload.password)
        changes["password"] = "***"

    await db.commit()
    await db.refresh(user)

    await audit(
        db,
        action="user.updated",
        resource="user",
        resource_id=user.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return user
