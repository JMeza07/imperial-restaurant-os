from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service


router = APIRouter()

admin_router = APIRouter(
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Datos del usuario autenticado",
)
async def me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@admin_router.get(
    "/users",
    response_model=List[UserRead],
    summary="Listar usuarios",
)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await user_service.list_users(db, skip=skip, limit=limit)


@admin_router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
)
async def create_user(
    payload: UserCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await user_service.create_user(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Consultar usuario",
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await user_service.get_user(db, user_id)


@admin_router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Actualizar usuario",
)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await user_service.update_user(
        db=db,
        user_id=user_id,
        payload=payload,
        request=request,
        actor=current_user,
    )
