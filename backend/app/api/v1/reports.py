from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.reports import (
    CashSummaryRead,
    CategorySalesRead,
    CommissionSummaryRead,
    DailySalesRead,
    EmployeePerformanceRead,
    InventoryConsumptionRead,
    PaymentMethodSalesRead,
    ReportSummaryRead,
    SurveySummaryRead,
    TopDishRead,
)
from app.services import reports_service


admin_router = APIRouter()


@admin_router.get(
    "/reportes/resumen",
    response_model=ReportSummaryRead,
    summary="Dashboard resumen",
)
async def report_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    branch_id: UUID | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await reports_service.get_report_summary(
        db=db,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
    )


@admin_router.get(
    "/reportes/ventas/diarias",
    response_model=List[DailySalesRead],
    summary="Ventas por día",
)
async def daily_sales(
    date_from: date | None = None,
    date_to: date | None = None,
    branch_id: UUID | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await reports_service.get_daily_sales(
        db=db,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
    )


@admin_router.get(
    "/reportes/ventas/categorias",
    response_model=List[CategorySalesRead],
    summary="Ventas por categoría",
)
async def sales_by_category(
    date_from: date | None = None,
    date_to: date | None = None,
    branch_id: UUID | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await reports_service.get_sales_by_category(
        db=db,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
    )


@admin_router.get(
    "/reportes/platos/mas-vendidos",
    response_model=List[TopDishRead],
    summary="Platos más vendidos",
)
async def top_dishes(
    date_from: date | None = None,
    date_to: date | None = None,
    branch_id: UUID | None = None,
    limit: int = 20,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await reports_service.get_top_dishes(
        db=db,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
        limit=limit,
    )


@admin_router.get(
    "/reportes/ventas/metodos-pago",
    response_model=List[PaymentMethodSalesRead],
    summary="Ventas por método de pago",
)
async def sales_by_payment_method(
    date_from: date | None = None,
    date_to: date | None = None,
    branch_id: UUID | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await reports_service.get_sales_by_payment_method(
        db=db,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
    )


@admin_router.get(
    "/reportes/empleados/rendimiento",
    response_model=List[EmployeePerformanceRead],
    summary="Rendimiento de empleados",
)
async def employee_performance(
    date_from: date | None = None,
    date_to: date | None = None,
    branch_id: UUID | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await reports_service.get_employee_performance(
        db=db,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
    )


@admin_router.get(
    "/reportes/encuestas/resumen",
    response_model=SurveySummaryRead,
    summary="Resumen de encuestas",
)
async def survey_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    branch_id: UUID | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await reports_service.get_survey_summary(
        db=db,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
    )


@admin_router.get(
    "/reportes/comisiones/resumen",
    response_model=List[CommissionSummaryRead],
    summary="Resumen de comisiones",
)
async def commission_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await reports_service.get_commission_summary(
        db=db,
        date_from=date_from,
        date_to=date_to,
    )


@admin_router.get(
    "/reportes/caja/resumen",
    response_model=List[CashSummaryRead],
    summary="Resumen de caja por método de pago",
)
async def cash_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    branch_id: UUID | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await reports_service.get_cash_summary(
        db=db,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
    )


@admin_router.get(
    "/reportes/inventario/consumo",
    response_model=List[InventoryConsumptionRead],
    summary="Consumo, compras y desperdicio",
)
async def inventory_consumption(
    date_from: date | None = None,
    date_to: date | None = None,
    branch_id: UUID | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await reports_service.get_inventory_consumption(
        db=db,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
    )
