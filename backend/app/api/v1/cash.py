from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import (
    CashSessionCloseRequest,
    CashSessionOpenRequest,
    CashSessionRead,
)
from app.services import payment_service


admin_router = APIRouter()


@admin_router.post(
    "/caja/abrir",
    response_model=CashSessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir sesión de caja",
)
async def open_cash_session(
    payload: CashSessionOpenRequest,
    request: Request,
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.CAJERO,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.open_cash_session(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/caja/actual",
    response_model=CashSessionRead,
    summary="Consultar caja abierta",
)
async def get_open_cash_session(
    branch_id: UUID | None = None,
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.CAJERO,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.get_open_cash_session(db, branch_id)


@admin_router.post(
    "/caja/{session_id}/cerrar",
    response_model=CashSessionRead,
    summary="Cerrar sesión de caja",
)
async def close_cash_session(
    session_id: UUID,
    payload: CashSessionCloseRequest,
    request: Request,
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.CAJERO,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.close_cash_session(
        db=db,
        session_id=session_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )
