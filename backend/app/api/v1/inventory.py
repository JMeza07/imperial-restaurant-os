from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import PurchaseOrderStatus, StockMovementType, UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.inventory import (
    PurchaseOrderCreate,
    PurchaseOrderRead,
    StockAdjustmentRequest,
    StockItemRead,
    StockItemUpdate,
    StockMovementRead,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
    WasteCreate,
    WasteRead,
)
from app.services import inventory_service


admin_router = APIRouter()


@admin_router.get(
    "/inventario/stock",
    response_model=List[StockItemRead],
    summary="Consultar stock",
)
async def list_stock(
    branch_id: UUID | None = None,
    low_stock: bool = False,
    search: str | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.list_stock(
        db=db,
        branch_id=branch_id,
        low_stock=low_stock,
        search=search,
    )


@admin_router.post(
    "/inventario/stock/inicializar",
    summary="Inicializar registros de stock",
)
async def initialize_stock(
    branch_id: UUID | None = None,
    request: Request = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.initialize_stock(
        db=db,
        branch_id=branch_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.patch(
    "/inventario/stock/{stock_id}",
    response_model=StockItemRead,
    summary="Actualizar stock mínimo",
)
async def update_stock_item(
    stock_id: UUID,
    payload: StockItemUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.update_stock_item(
        db=db,
        stock_id=stock_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.post(
    "/inventario/ajustes",
    response_model=StockMovementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar ajuste manual de inventario",
)
async def adjust_stock(
    payload: StockAdjustmentRequest,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.adjust_stock(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/inventario/movimientos",
    response_model=List[StockMovementRead],
    summary="Consultar movimientos de inventario",
)
async def list_movements(
    branch_id: UUID | None = None,
    ingredient_id: UUID | None = None,
    movement_type: StockMovementType | None = None,
    limit: int = 200,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.list_movements(
        db=db,
        branch_id=branch_id,
        ingredient_id=ingredient_id,
        movement_type=movement_type,
        limit=limit,
    )


@admin_router.get(
    "/inventario/alertas",
    response_model=List[StockItemRead],
    summary="Consultar alertas de stock bajo",
)
async def list_alerts(
    branch_id: UUID | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.list_low_stock_alerts(
        db=db,
        branch_id=branch_id,
    )


@admin_router.get(
    "/inventario/proveedores",
    response_model=List[SupplierRead],
    summary="Listar proveedores",
)
async def list_suppliers(
    include_inactive: bool = False,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.list_suppliers(db, include_inactive)


@admin_router.post(
    "/inventario/proveedores",
    response_model=SupplierRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proveedor",
)
async def create_supplier(
    payload: SupplierCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.create_supplier(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.patch(
    "/inventario/proveedores/{supplier_id}",
    response_model=SupplierRead,
    summary="Actualizar proveedor",
)
async def update_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.update_supplier(
        db=db,
        supplier_id=supplier_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/inventario/compras",
    response_model=List[PurchaseOrderRead],
    summary="Listar órdenes de compra",
)
async def list_purchase_orders(
    supplier_id: UUID | None = None,
    purchase_status: PurchaseOrderStatus | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.list_purchase_orders(
        db=db,
        supplier_id=supplier_id,
        purchase_status=purchase_status,
    )


@admin_router.post(
    "/inventario/compras",
    response_model=PurchaseOrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear orden de compra",
)
async def create_purchase_order(
    payload: PurchaseOrderCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.create_purchase_order(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/inventario/compras/{purchase_id}",
    response_model=PurchaseOrderRead,
    summary="Consultar orden de compra",
)
async def get_purchase_order(
    purchase_id: UUID,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.get_purchase_order(db, purchase_id)


@admin_router.post(
    "/inventario/compras/{purchase_id}/recibir",
    response_model=PurchaseOrderRead,
    summary="Recibir orden de compra",
)
async def receive_purchase_order(
    purchase_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.receive_purchase_order(
        db=db,
        purchase_id=purchase_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.post(
    "/inventario/desperdicios",
    response_model=WasteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar desperdicio",
)
async def create_waste_event(
    payload: WasteCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.create_waste_event(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )
