from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import (
    CommissionEventStatus,
    CommissionPeriodStatus,
    CommissionPayoutStatus,
    UserRole,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.commissions import (
    AssignWaiterRequest,
    CommissionEventRead,
    CommissionPayoutRead,
    CommissionPeriodCreate,
    CommissionPeriodRead,
    CommissionRuleCreate,
    CommissionRuleRead,
    CommissionRuleUpdate,
    PayoutPayRequest,
    SurveyCreateRequest,
    SurveyRead,
)
from app.services import commissions_service


router = APIRouter()
admin_router = APIRouter()


@router.post(
    "/ordenes/{order_id}/encuesta",
    response_model=SurveyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar encuesta de satisfacción",
)
async def create_survey(
    order_id: UUID,
    payload: SurveyCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.create_survey(
        db=db,
        order_id=order_id,
        payload=payload,
        request=request,
    )


@admin_router.get(
    "/comisiones/reglas",
    response_model=List[CommissionRuleRead],
    summary="Listar reglas de comisión",
)
async def list_rules(
    include_inactive: bool = False,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.list_rules(db, include_inactive)


@admin_router.post(
    "/comisiones/reglas",
    response_model=CommissionRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear regla de comisión",
)
async def create_rule(
    payload: CommissionRuleCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.create_rule(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.patch(
    "/comisiones/reglas/{rule_id}",
    response_model=CommissionRuleRead,
    summary="Actualizar regla de comisión",
)
async def update_rule(
    rule_id: UUID,
    payload: CommissionRuleUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.update_rule(
        db=db,
        rule_id=rule_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/comisiones/periodos",
    response_model=List[CommissionPeriodRead],
    summary="Listar periodos de comisión",
)
async def list_periods(
    period_status: CommissionPeriodStatus | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.list_periods(db, period_status)


@admin_router.post(
    "/comisiones/periodos",
    response_model=CommissionPeriodRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear periodo de comisión",
)
async def create_period(
    payload: CommissionPeriodCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.create_period(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/comisiones/periodos/{period_id}",
    summary="Detalle de periodo",
)
async def get_period(
    period_id: UUID,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    period = await commissions_service.get_period(db, period_id)

    total_calculated = sum(
        event.amount
        for event in period.events
        if event.status != CommissionEventStatus.ANULADA
    )

    total_approved = sum(
        event.amount
        for event in period.events
        if event.status == CommissionEventStatus.APROBADA
    )

    total_paid = sum(
        payout.amount
        for payout in period.payouts
        if payout.status == CommissionPayoutStatus.PAGADO
    )

    return {
        "period": CommissionPeriodRead.model_validate(period),
        "events": [
            CommissionEventRead.model_validate(event)
            for event in period.events
        ],
        "payouts": [
            CommissionPayoutRead.model_validate(payout)
            for payout in period.payouts
        ],
        "total_calculated": str(total_calculated),
        "total_approved": str(total_approved),
        "total_paid": str(total_paid),
    }


@admin_router.post(
    "/comisiones/periodos/{period_id}/calcular",
    summary="Calcular periodo",
)
async def calculate_period(
    period_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.calculate_period(
        db=db,
        period_id=period_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.post(
    "/comisiones/periodos/{period_id}/aprobar",
    response_model=CommissionPeriodRead,
    summary="Aprobar periodo",
)
async def approve_period(
    period_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.approve_period(
        db=db,
        period_id=period_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.post(
    "/comisiones/periodos/{period_id}/generar-pagos",
    summary="Generar pagos de comisiones",
)
async def generate_payouts(
    period_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.generate_payouts(
        db=db,
        period_id=period_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/comisiones/eventos",
    response_model=List[CommissionEventRead],
    summary="Listar eventos de comisión",
)
async def list_events(
    period_id: UUID | None = None,
    employee_id: UUID | None = None,
    event_status: CommissionEventStatus | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.list_events(
        db=db,
        period_id=period_id,
        employee_id=employee_id,
        event_status=event_status,
    )


@admin_router.patch(
    "/comisiones/eventos/{event_id}/anular",
    response_model=CommissionEventRead,
    summary="Anular evento de comisión",
)
async def annul_event(
    event_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.annul_event(
        db=db,
        event_id=event_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/comisiones/pagos",
    response_model=List[CommissionPayoutRead],
    summary="Listar pagos de comisiones",
)
async def list_payouts(
    period_id: UUID | None = None,
    employee_id: UUID | None = None,
    payout_status: CommissionPayoutStatus | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.list_payouts(
        db=db,
        period_id=period_id,
        employee_id=employee_id,
        payout_status=payout_status,
    )


@admin_router.post(
    "/comisiones/pagos/{payout_id}/pagar",
    response_model=CommissionPayoutRead,
    summary="Pagar comisión",
)
async def pay_payout(
    payout_id: UUID,
    payload: PayoutPayRequest,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.pay_payout(
        db=db,
        payout_id=payout_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.post(
    "/comisiones/pagos/{payout_id}/anular",
    response_model=CommissionPayoutRead,
    summary="Anular pago de comisión",
)
async def annul_payout(
    payout_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await commissions_service.annul_payout(
        db=db,
        payout_id=payout_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.patch(
    "/ordenes/{order_id}/mesero",
    summary="Asignar mesero responsable a una orden",
)
async def assign_waiter(
    order_id: UUID,
    payload: AssignWaiterRequest,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    order = await commissions_service.assign_waiter_to_order(
        db=db,
        order_id=order_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )

    return {
        "order_id": str(order.id),
        "waiter_id": str(order.waiter_id),
    }
