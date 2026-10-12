from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import OrderStatus, OrderType, UserRole
from app.db.session import get_db
from app.schemas.order import CreateOrderRequest, OrderItemRead, OrderRead
from app.services import order_service


router = APIRouter()
admin_router = APIRouter()


@router.post(
    "/ordenes",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear orden o adicionar platos a la orden abierta",
)
async def create_order(
    payload: CreateOrderRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await order_service.create_or_extend_order(
        db=db,
        payload=payload,
        request=request,
    )


@router.get(
    "/ordenes/{order_id}",
    response_model=OrderRead,
    summary="Consultar orden pública por QR",
)
async def get_order_public(
    order_id: UUID,
    codigo_qr: str,
    db: AsyncSession = Depends(get_db),
):
    return await order_service.get_order_public(
        db=db,
        order_id=order_id,
        codigo_qr=codigo_qr,
    )


@admin_router.get(
    "/ordenes",
    response_model=List[OrderRead],
    summary="Dashboard de órdenes",
)
async def list_orders(
    order_status: OrderStatus | None = None,
    table_id: UUID | None = None,
    order_type: OrderType | None = None,
    current_user=Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.list_orders_admin(
        db=db,
        order_status=order_status,
        table_id=table_id,
        order_type=order_type,
    )


@admin_router.get(
    "/ordenes/{order_id}",
    response_model=OrderRead,
    summary="Consultar orden administrativamente",
)
async def get_order_admin(
    order_id: UUID,
    current_user=Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.get_order_admin(db, order_id)


@admin_router.patch(
    "/detalles/{item_id}/cancelar",
    response_model=OrderItemRead,
    summary="Cancelar plato en estado RECIBIDO",
)
async def cancel_order_item(
    item_id: UUID,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.cancel_order_item(
        db=db,
        order_item_id=item_id,
        request=request,
        actor_user=current_user,
    )
