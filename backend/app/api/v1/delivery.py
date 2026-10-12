from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.enums import DeliveryStatus, OrderStatus, UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.delivery import (
    DeliveryAssignRequest,
    DeliveryCreateRequest,
    DeliveryRead,
    DeliveryTrackingRead,
    DeliveryZoneCreate,
    DeliveryZoneRead,
    DeliveryZoneUpdate,
)
from app.services import delivery_service


router = APIRouter()
admin_router = APIRouter()


@router.post(
    "/domicilios",
    response_model=DeliveryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear pedido a domicilio",
)
async def create_delivery_public(
    payload: DeliveryCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.create_delivery_order(
        db=db,
        payload=payload,
        request=request,
        actor_user=None,
    )


@router.get(
    "/domicilios/{order_id}/estado",
    response_model=DeliveryTrackingRead,
    summary="Consultar estado público de un domicilio",
)
async def get_delivery_tracking(
    order_id: UUID,
    telefono: str,
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.get_public_delivery_tracking(
        db=db,
        order_id=order_id,
        telefono=telefono,
    )


@admin_router.get(
    "/domicilios/zonas",
    response_model=List[DeliveryZoneRead],
    summary="Listar zonas de domicilio",
)
async def list_delivery_zones(
    include_inactive: bool = False,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.list_delivery_zones(db, include_inactive)


@admin_router.post(
    "/domicilios/zonas",
    response_model=DeliveryZoneRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear zona de domicilio",
)
async def create_delivery_zone(
    payload: DeliveryZoneCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.create_delivery_zone(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.patch(
    "/domicilios/zonas/{zone_id}",
    response_model=DeliveryZoneRead,
    summary="Actualizar zona de domicilio",
)
async def update_delivery_zone(
    zone_id: UUID,
    payload: DeliveryZoneUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.update_delivery_zone(
        db=db,
        zone_id=zone_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/domicilios",
    response_model=List[DeliveryRead],
    summary="Listar domicilios",
)
async def list_deliveries(
    delivery_status: DeliveryStatus | None = None,
    order_status: OrderStatus | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.list_deliveries_admin(
        db=db,
        delivery_status=delivery_status,
        order_status=order_status,
    )


@admin_router.post(
    "/domicilios",
    response_model=DeliveryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear domicilio administrativamente",
)
async def create_delivery_admin(
    payload: DeliveryCreateRequest,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.create_delivery_order(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/domicilios/{delivery_id}",
    response_model=DeliveryRead,
    summary="Consultar domicilio",
)
async def get_delivery(
    delivery_id: UUID,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.get_delivery_admin(db, delivery_id)


@admin_router.patch(
    "/domicilios/{delivery_id}/asignar",
    response_model=DeliveryRead,
    summary="Asignar domiciliario",
)
async def assign_delivery(
    delivery_id: UUID,
    payload: DeliveryAssignRequest,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.assign_delivery(
        db=db,
        delivery_id=delivery_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.patch(
    "/domicilios/{delivery_id}/en-camino",
    response_model=DeliveryRead,
    summary="Marcar domicilio EN_CAMINO",
)
async def mark_en_camino(
    delivery_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.DOMICILIARIO, UserRole.ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.mark_delivery_en_camino(
        db=db,
        delivery_id=delivery_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.patch(
    "/domicilios/{delivery_id}/entregado",
    response_model=DeliveryRead,
    summary="Marcar domicilio ENTREGADO",
)
async def mark_entregado(
    delivery_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.DOMICILIARIO, UserRole.ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.mark_delivery_entregado(
        db=db,
        delivery_id=delivery_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.patch(
    "/domicilios/{delivery_id}/cancelar",
    response_model=DeliveryRead,
    summary="Cancelar domicilio",
)
async def cancel_delivery(
    delivery_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await delivery_service.cancel_delivery(
        db=db,
        delivery_id=delivery_id,
        request=request,
        actor_user=current_user,
    )
