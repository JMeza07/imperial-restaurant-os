from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_current_user, require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import OrderRead
from app.schemas.payment import CloseOrderRequest, PaymentCreateRequest, PaymentRead
from app.services import payment_service


router = APIRouter()
admin_router = APIRouter()


@router.post(
    "/ordenes/{order_id}/cierre",
    response_model=OrderRead,
    summary="Cerrar cuenta de una orden",
)
async def close_order(
    order_id: UUID,
    payload: CloseOrderRequest,
    request: Request,
    codigo_qr: Optional[str] = Query(default=None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user:
        if current_user.role not in (
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.CAJERO,
            UserRole.MESERO,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para cerrar la orden",
            )
    else:
        qr = codigo_qr or payload.codigo_qr or request.query_params.get("codigo_qr")
        if not qr:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autenticado o código QR requerido para cerrar la orden",
            )
        order = await payment_service._get_order_by_id(db, order_id)
        table = await payment_service._get_table_by_qr(db, qr)
        if order.table_id != table.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El código QR no corresponde a la mesa de esta orden",
            )

    return await payment_service.close_order(
        db=db,
        order_id=order_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@router.post(
    "/ordenes/{order_id}/pagos",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar pago público con QR",
)
async def create_payment_public(
    order_id: UUID,
    payload: PaymentCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.register_payment_public(
        db=db,
        order_id=order_id,
        payload=payload,
        request=request,
    )


@admin_router.post(
    "/ordenes/{order_id}/pagos",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar pago administrativo",
)
async def create_payment_admin(
    order_id: UUID,
    payload: PaymentCreateRequest,
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
    return await payment_service.register_payment_admin(
        db=db,
        order_id=order_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/ordenes/{order_id}/pagos",
    response_model=List[PaymentRead],
    summary="Listar pagos de una orden",
)
async def list_order_payments(
    order_id: UUID,
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.CAJERO,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.list_order_payments(db, order_id)
