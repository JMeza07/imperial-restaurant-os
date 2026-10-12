from collections import defaultdict
from datetime import datetime, time, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import (
    CommissionEventStatus,
    CommissionPeriodStatus,
    CommissionPayoutStatus,
    CommissionRuleType,
    DeliveryStatus,
    OrderItemStatus,
    OrderStatus,
    OrderType,
    UserRole,
)
from app.models.commissions import (
    CommissionEvent,
    CommissionPayout,
    CommissionPeriod,
    CommissionRule,
    Survey,
)
from app.models.delivery import Delivery
from app.models.order import Order, OrderItem
from app.models.turnos import Employee
from app.models.user import User
from app.schemas.commissions import (
    AssignWaiterRequest,
    CommissionPeriodCreate,
    CommissionRuleCreate,
    CommissionRuleUpdate,
    PayoutPayRequest,
    SurveyCreateRequest,
)
from app.services.audit_service import audit
from app.services.order_service import _get_table_by_qr, register_event
from app.services.payment_service import round_money


def is_percent_rule(rule_type: CommissionRuleType) -> bool:
    return rule_type in (
        CommissionRuleType.PERCENT_NET_SALES,
        CommissionRuleType.PERCENT_ITEM_SALES,
    )


def calculate_commission_amount(
    rule_type: CommissionRuleType,
    value: Decimal,
    base_amount: Decimal = Decimal("0"),
    quantity: int = 1,
) -> Decimal:
    if rule_type == CommissionRuleType.PERCENT_NET_SALES:
        return round_money(base_amount * value / Decimal("100"))

    if rule_type == CommissionRuleType.PERCENT_ITEM_SALES:
        return round_money(base_amount * value / Decimal("100"))

    if rule_type == CommissionRuleType.FIXED_PER_ITEM:
        return round_money(value * quantity)

    return round_money(value)


def apply_order_cap(amount: Decimal, cap: Optional[Decimal]) -> Decimal:
    if cap is None:
        return amount

    return min(amount, cap)


def apply_period_cap(
    amount: Decimal,
    cap: Optional[Decimal],
    used: Decimal,
) -> Decimal:
    if cap is None:
        return amount

    remaining = cap - used

    if remaining <= 0:
        return Decimal("0")

    return min(amount, remaining)


async def _employee_by_user(
    db: AsyncSession,
    user_id: Optional[UUID],
    cache: Dict[UUID, Optional[Employee]],
) -> Optional[Employee]:
    if not user_id:
        return None

    if user_id in cache:
        return cache[user_id]

    employee = await db.scalar(
        select(Employee)
        .options(selectinload(Employee.user))
        .where(Employee.user_id == user_id)
    )

    cache[user_id] = employee

    return employee


async def _get_order_employee(
    db: AsyncSession,
    rule_role: str,
    order: Order,
    delivery: Optional[Delivery],
    cache: Dict[UUID, Optional[Employee]],
) -> Optional[Employee]:
    if rule_role == UserRole.MESERO.value:
        return await _employee_by_user(db, order.waiter_id, cache)

    if rule_role == UserRole.DOMICILIARIO.value:
        if delivery and delivery.assigned_domiciliario_id:
            return await _employee_by_user(
                db,
                delivery.assigned_domiciliario_id,
                cache,
            )

        return None

    return None


async def _get_item_employee(
    db: AsyncSession,
    rule_role: str,
    order: Order,
    item: OrderItem,
    delivery: Optional[Delivery],
    cache: Dict[UUID, Optional[Employee]],
) -> Optional[Employee]:
    if rule_role == UserRole.COCINERO.value:
        user_id = item.prepared_by_user_id or item.ready_by_user_id
        return await _employee_by_user(db, user_id, cache)

    return await _get_order_employee(db, rule_role, order, delivery, cache)


def _rule_active_for_date(rule: CommissionRuleType, target_date) -> bool:
    if not rule.is_active:
        return False

    if rule.starts_at and target_date < rule.starts_at:
        return False

    if rule.ends_at and target_date > rule.ends_at:
        return False

    return True


def _rule_matches_order(rule: CommissionRule, order: Order) -> bool:
    conditions = rule.conditions or {}

    order_types = conditions.get("order_types")

    if order_types and order.order_type.value not in order_types:
        return False

    channels = conditions.get("channels")

    if channels and order.channel.value not in channels:
        return False

    return True


def _rule_matches_item(rule: CommissionRule, item: OrderItem) -> bool:
    conditions = rule.conditions or {}

    dish_ids = conditions.get("dish_ids")

    if dish_ids and str(item.dish_id) not in dish_ids:
        return False

    category_ids = conditions.get("category_ids")

    if category_ids:
        if not item.dish:
            return False

        if str(item.dish.category_id) not in category_ids:
            return False

    return True


async def list_rules(
    db: AsyncSession,
    include_inactive: bool = False,
) -> List[CommissionRule]:
    query = select(CommissionRule).order_by(CommissionRule.priority.desc())

    if not include_inactive:
        query = query.where(CommissionRule.is_active.is_(True))

    return (await db.scalars(query)).all()


async def create_rule(
    db: AsyncSession,
    payload: CommissionRuleCreate,
    request: Request | None = None,
    actor_user=None,
) -> CommissionRule:
    rule = CommissionRule(
        name=payload.name,
        role=payload.role.value,
        rule_type=payload.rule_type,
        value=payload.value,
        cap_per_order=payload.cap_per_order,
        cap_per_period=payload.cap_per_period,
        conditions=payload.conditions,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        priority=payload.priority,
        is_active=payload.is_active,
    )

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    await audit(
        db,
        action="commission_rule.created",
        resource="commission_rule",
        resource_id=rule.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={"name": rule.name},
    )

    return rule


async def update_rule(
    db: AsyncSession,
    rule_id: UUID,
    payload: CommissionRuleUpdate,
    request: Request | None = None,
    actor_user=None,
) -> CommissionRule:
    rule = await db.get(CommissionRule, rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla de comisión no encontrada",
        )

    data = payload.model_dump(exclude_unset=True)

    if payload.role is not None:
        data["role"] = payload.role.value

    for field, value in data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)

    await audit(
        db,
        action="commission_rule.updated",
        resource="commission_rule",
        resource_id=rule.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={"name": rule.name},
    )

    return rule


async def create_period(
    db: AsyncSession,
    payload: CommissionPeriodCreate,
    request: Request | None = None,
    actor_user=None,
) -> CommissionPeriod:
    period = CommissionPeriod(
        branch_id=payload.branch_id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.notes,
        status=CommissionPeriodStatus.ABIERTA,
    )

    db.add(period)
    await db.commit()
    await db.refresh(period)

    await audit(
        db,
        action="commission_period.created",
        resource="commission_period",
        resource_id=period.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "start_date": str(period.start_date),
            "end_date": str(period.end_date),
        },
    )

    return period


async def list_periods(
    db: AsyncSession,
    period_status: Optional[CommissionPeriodStatus] = None,
) -> List[CommissionPeriod]:
    query = select(CommissionPeriod).options(
        selectinload(CommissionPeriod.branch)
    )

    if period_status:
        query = query.where(CommissionPeriod.status == period_status)

    query = query.order_by(CommissionPeriod.created_at.desc())

    return (await db.scalars(query)).all()


async def get_period(
    db: AsyncSession,
    period_id: UUID,
) -> CommissionPeriod:
    period = await db.scalar(
        select(CommissionPeriod)
        .options(
            selectinload(CommissionPeriod.branch),
            selectinload(CommissionPeriod.events).selectinload(
                CommissionEvent.employee
            ).selectinload(Employee.user),
            selectinload(CommissionPeriod.events).selectinload(
                CommissionEvent.rule
            ),
            selectinload(CommissionPeriod.payouts).selectinload(
                CommissionPayout.employee
            ).selectinload(Employee.user),
        )
        .where(CommissionPeriod.id == period_id)
    )

    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Periodo de comisión no encontrado",
        )

    return period


async def calculate_period(
    db: AsyncSession,
    period_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> dict:
    period = await get_period(db, period_id)

    if period.status not in (
        CommissionPeriodStatus.ABIERTA,
        CommissionPeriodStatus.CALCULADA,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede recalcular un periodo aprobado o pagado",
        )

    paid_payouts = await db.scalar(
        select(func.count(CommissionPayout.id)).where(
            CommissionPayout.period_id == period.id,
            CommissionPayout.status == CommissionPayoutStatus.PAGADO,
        )
    )

    if paid_payouts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede recalcular un periodo con pagos ya pagados",
        )

    await db.execute(
        delete(CommissionPayout).where(
            CommissionPayout.period_id == period.id
        )
    )

    await db.execute(
        delete(CommissionEvent).where(
            CommissionEvent.period_id == period.id
        )
    )

    start_dt = datetime.combine(
        period.start_date,
        time.min,
        tzinfo=timezone.utc,
    )

    end_dt = datetime.combine(
        period.end_date,
        time.max,
        tzinfo=timezone.utc,
    )

    orders_query = (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.dish),
        )
        .where(
            Order.status.in_(
                [
                    OrderStatus.PAGADA,
                    OrderStatus.ENCUESTADA,
                ]
            ),
            Order.paid_at >= start_dt,
            Order.paid_at <= end_dt,
        )
    )

    if period.branch_id:
        orders_query = orders_query.where(
            Order.branch_id == period.branch_id
        )

    orders = (await db.scalars(orders_query)).all()

    order_ids = [order.id for order in orders]

    deliveries_by_order = {}

    if order_ids:
        deliveries = await db.scalars(
            select(Delivery).where(Delivery.order_id.in_(order_ids))
        )

        deliveries_by_order = {
            delivery.order_id: delivery
            for delivery in deliveries.all()
        }

    surveys_by_order = {}

    if order_ids:
        surveys = await db.scalars(
            select(Survey).where(Survey.order_id.in_(order_ids))
        )

        surveys_by_order = {
            survey.order_id: survey
            for survey in surveys.all()
        }

    rules = await db.scalars(
        select(CommissionRule)
        .where(CommissionRule.is_active.is_(True))
        .order_by(CommissionRule.priority.desc())
    ).all()

    employee_cache: Dict[UUID, Optional[Employee]] = {}
    period_caps = defaultdict(lambda: Decimal("0"))

    created = 0
    total_amount = Decimal("0")

    for order in orders:
        if not order.paid_at:
            continue

        paid_date = order.paid_at.date()
        delivery = deliveries_by_order.get(order.id)
        survey = surveys_by_order.get(order.id)

        net_sales = max(
            Decimal("0"),
            (order.subtotal or Decimal("0")) - (order.discount_amount or Decimal("0")),
        )

        for rule in rules:
            if not _rule_active_for_date(rule, paid_date):
                continue

            if not _rule_matches_order(rule, order):
                continue

            if rule.rule_type in (
                CommissionRuleType.PERCENT_ITEM_SALES,
                CommissionRuleType.FIXED_PER_ITEM,
            ):
                aggregates = {}

                for item in order.items:
                    if item.status == OrderItemStatus.CANCELADO:
                        continue

                    if not _rule_matches_item(rule, item):
                        continue

                    employee = await _get_item_employee(
                        db=db,
                        rule_role=rule.role,
                        order=order,
                        item=item,
                        delivery=delivery,
                        cache=employee_cache,
                    )

                    if not employee:
                        continue

                    key = employee.id

                    if key not in aggregates:
                        aggregates[key] = {
                            "employee": employee,
                            "base": Decimal("0"),
                            "quantity": 0,
                        }

                    aggregates[key]["base"] += item.subtotal
                    aggregates[key]["quantity"] += item.quantity

                for aggregate in aggregates.values():
                    employee = aggregate["employee"]

                    if rule.rule_type == CommissionRuleType.PERCENT_ITEM_SALES:
                        base_amount = aggregate["base"]
                        quantity = 1
                    else:
                        base_amount = Decimal(aggregate["quantity"])
                        quantity = aggregate["quantity"]

                    amount = calculate_commission_amount(
                        rule_type=rule.rule_type,
                        value=rule.value,
                        base_amount=base_amount,
                        quantity=quantity,
                    )

                    amount = apply_order_cap(amount, rule.cap_per_order)

                    cap_key = (rule.id, employee.id)
                    amount = apply_period_cap(
                        amount=amount,
                        cap=rule.cap_per_period,
                        used=period_caps[cap_key],
                    )

                    if amount <= 0:
                        continue

                    period_caps[cap_key] += amount

                    dedup_key = (
                        f"period:{period.id}:"
                        f"rule:{rule.id}:"
                        f"order:{order.id}:"
                        f"employee:{employee.id}:"
                        f"type:item"
                    )

                    event = CommissionEvent(
                        period_id=period.id,
                        rule_id=rule.id,
                        employee_id=employee.id,
                        order_id=order.id,
                        order_item_id=None,
                        base_amount=base_amount,
                        amount=amount,
                        status=CommissionEventStatus.CALCULADA,
                        dedup_key=dedup_key,
                        detail={
                            "order_display_code": order.display_code,
                            "rule_type": rule.rule_type.value,
                        },
                    )

                    db.add(event)
                    created += 1
                    total_amount += amount

            else:
                employee = await _get_order_employee(
                    db=db,
                    rule_role=rule.role,
                    order=order,
                    delivery=delivery,
                    cache=employee_cache,
                )

                if not employee:
                    continue

                if rule.rule_type == CommissionRuleType.PERCENT_NET_SALES:
                    base_amount = net_sales
                    amount = calculate_commission_amount(
                        rule_type=rule.rule_type,
                        value=rule.value,
                        base_amount=base_amount,
                    )

                elif rule.rule_type == CommissionRuleType.FIXED_PER_ORDER:
                    base_amount = Decimal("1")
                    amount = calculate_commission_amount(
                        rule_type=rule.rule_type,
                        value=rule.value,
                    )

                elif rule.rule_type == CommissionRuleType.FIXED_PER_DELIVERY:
                    if (
                        order.order_type != OrderType.DOMICILIO
                        or not delivery
                        or delivery.status != DeliveryStatus.ENTREGADO
                    ):
                        continue

                    base_amount = Decimal("1")
                    amount = calculate_commission_amount(
                        rule_type=rule.rule_type,
                        value=rule.value,
                    )

                elif rule.rule_type == CommissionRuleType.SURVEY_BONUS_FIXED:
                    min_score = int(
                        (rule.conditions or {}).get("min_survey_score", 0)
                    )

                    if not survey or survey.general_score < min_score:
                        continue

                    base_amount = Decimal(str(survey.general_score))
                    amount = calculate_commission_amount(
                        rule_type=rule.rule_type,
                        value=rule.value,
                    )

                else:
                    continue

                amount = apply_order_cap(amount, rule.cap_per_order)

                cap_key = (rule.id, employee.id)
                amount = apply_period_cap(
                    amount=amount,
                    cap=rule.cap_per_period,
                    used=period_caps[cap_key],
                )

                if amount <= 0:
                    continue

                period_caps[cap_key] += amount

                dedup_key = (
                    f"period:{period.id}:"
                    f"rule:{rule.id}:"
                    f"order:{order.id}:"
                    f"employee:{employee.id}:"
                    f"type:order"
                )

                event = CommissionEvent(
                    period_id=period.id,
                    rule_id=rule.id,
                    employee_id=employee.id,
                    order_id=order.id,
                    order_item_id=None,
                    base_amount=base_amount,
                    amount=amount,
                    status=CommissionEventStatus.CALCULADA,
                    dedup_key=dedup_key,
                    detail={
                        "order_display_code": order.display_code,
                        "rule_type": rule.rule_type.value,
                    },
                )

                db.add(event)
                created += 1
                total_amount += amount

    period.status = CommissionPeriodStatus.CALCULADA
    period.calculated_at = datetime.now(timezone.utc)
    period.approved_at = None
    period.paid_at = None

    await db.commit()

    await audit(
        db,
        action="commission_period.calculated",
        resource="commission_period",
        resource_id=period.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "created_events": created,
            "total_amount": str(round_money(total_amount)),
        },
    )

    return {
        "created": created,
        "total": str(round_money(total_amount)),
    }


async def approve_period(
    db: AsyncSession,
    period_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> CommissionPeriod:
    period = await get_period(db, period_id)

    if period.status != CommissionPeriodStatus.CALCULADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se puede aprobar un periodo calculado",
        )

    events = await db.scalars(
        select(CommissionEvent).where(
            CommissionEvent.period_id == period.id,
            CommissionEvent.status == CommissionEventStatus.CALCULADA,
        )
    ).all()

    for event in events:
        event.status = CommissionEventStatus.APROBADA

    period.status = CommissionPeriodStatus.APROBADA
    period.approved_at = datetime.now(timezone.utc)

    await db.commit()

    await audit(
        db,
        action="commission_period.approved",
        resource="commission_period",
        resource_id=period.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
    )

    return await get_period(db, period.id)


async def generate_payouts(
    db: AsyncSession,
    period_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> dict:
    period = await get_period(db, period_id)

    if period.status != CommissionPeriodStatus.APROBADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se pueden generar pagos en un periodo aprobado",
        )

    paid_payouts = await db.scalar(
        select(func.count(CommissionPayout.id)).where(
            CommissionPayout.period_id == period.id,
            CommissionPayout.status == CommissionPayoutStatus.PAGADO,
        )
    )

    if paid_payouts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se pueden regenerar pagos porque ya hay pagos pagados",
        )

    await db.execute(
        delete(CommissionPayout).where(
            CommissionPayout.period_id == period.id
        )
    )

    rows = await db.execute(
        select(
            CommissionEvent.employee_id,
            func.sum(CommissionEvent.amount),
        )
        .where(
            CommissionEvent.period_id == period.id,
            CommissionEvent.status == CommissionEventStatus.APROBADA,
        )
        .group_by(CommissionEvent.employee_id)
    )

    created = 0

    for employee_id, amount in rows.all():
        amount_value = round_money(Decimal(str(amount)))

        if amount_value <= 0:
            continue

        payout = CommissionPayout(
            period_id=period.id,
            employee_id=employee_id,
            amount=amount_value,
            status=CommissionPayoutStatus.PENDIENTE,
        )

        db.add(payout)
        created += 1

    await db.commit()

    await audit(
        db,
        action="commission_payouts.generated",
        resource="commission_period",
        resource_id=period.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={"created_payouts": created},
    )

    return {
        "created": created,
    }


async def list_events(
    db: AsyncSession,
    period_id: Optional[UUID] = None,
    employee_id: Optional[UUID] = None,
    event_status: Optional[CommissionEventStatus] = None,
) -> List[CommissionEvent]:
    query = select(CommissionEvent).options(
        selectinload(CommissionEvent.employee).selectinload(Employee.user),
        selectinload(CommissionEvent.rule),
    )

    if period_id:
        query = query.where(CommissionEvent.period_id == period_id)

    if employee_id:
        query = query.where(CommissionEvent.employee_id == employee_id)

    if event_status:
        query = query.where(CommissionEvent.status == event_status)

    query = query.order_by(CommissionEvent.created_at.desc())

    return (await db.scalars(query)).all()


async def list_payouts(
    db: AsyncSession,
    period_id: Optional[UUID] = None,
    employee_id: Optional[UUID] = None,
    payout_status: Optional[CommissionPayoutStatus] = None,
) -> List[CommissionPayout]:
    query = select(CommissionPayout).options(
        selectinload(CommissionPayout.employee).selectinload(Employee.user),
    )

    if period_id:
        query = query.where(CommissionPayout.period_id == period_id)

    if employee_id:
        query = query.where(CommissionPayout.employee_id == employee_id)

    if payout_status:
        query = query.where(CommissionPayout.status == payout_status)

    query = query.order_by(CommissionPayout.created_at.desc())

    return (await db.scalars(query)).all()


async def pay_payout(
    db: AsyncSession,
    payout_id: UUID,
    payload: PayoutPayRequest,
    request: Request | None = None,
    actor_user=None,
) -> CommissionPayout:
    payout = await db.scalar(
        select(CommissionPayout)
        .options(
            selectinload(CommissionPayout.employee).selectinload(Employee.user)
        )
        .where(CommissionPayout.id == payout_id)
    )

    if not payout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago de comisión no encontrado",
        )

    if payout.status != CommissionPayoutStatus.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se puede pagar un pago pendiente",
        )

    payout.status = CommissionPayoutStatus.PAGADO
    payout.payment_method = payload.payment_method.value
    payout.reference = payload.reference
    payout.paid_at = datetime.now(timezone.utc)

    await db.commit()

    await audit(
        db,
        action="commission_payout.paid",
        resource="commission_payout",
        resource_id=payout.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "amount": str(payout.amount),
            "payment_method": payout.payment_method,
        },
    )

    period = await get_period(db, payout.period_id)

    pending_payouts = await db.scalar(
        select(func.count(CommissionPayout.id)).where(
            CommissionPayout.period_id == period.id,
            CommissionPayout.status == CommissionPayoutStatus.PENDIENTE,
        )
    )

    if pending_payouts == 0:
        period.status = CommissionPeriodStatus.PAGADA
        period.paid_at = datetime.now(timezone.utc)
        await db.commit()

    return payout


async def annul_event(
    db: AsyncSession,
    event_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> CommissionEvent:
    event = await db.scalar(
        select(CommissionEvent)
        .options(
            selectinload(CommissionEvent.employee).selectinload(Employee.user),
            selectinload(CommissionEvent.rule),
        )
        .where(CommissionEvent.id == event_id)
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento de comisión no encontrado",
        )

    period = await get_period(db, event.period_id)

    if period.status == CommissionPeriodStatus.PAGADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede anular un evento en un periodo pagado",
        )

    active_payouts = await db.scalar(
        select(func.count(CommissionPayout.id)).where(
            CommissionPayout.period_id == period.id,
            CommissionPayout.status != CommissionPayoutStatus.ANULADO,
        )
    )

    if active_payouts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Anule primero los pagos generados del periodo",
        )

    event.status = CommissionEventStatus.ANULADA

    await db.commit()

    await audit(
        db,
        action="commission_event.annulled",
        resource="commission_event",
        resource_id=event.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
    )

    return event


async def annul_payout(
    db: AsyncSession,
    payout_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> CommissionPayout:
    payout = await db.scalar(
        select(CommissionPayout)
        .options(
            selectinload(CommissionPayout.employee).selectinload(Employee.user)
        )
        .where(CommissionPayout.id == payout_id)
    )

    if not payout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago de comisión no encontrado",
        )

    if payout.status == CommissionPayoutStatus.PAGADO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede anular un pago ya pagado",
        )

    payout.status = CommissionPayoutStatus.ANULADO

    await db.commit()

    await audit(
        db,
        action="commission_payout.annulled",
        resource="commission_payout",
        resource_id=payout.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
    )

    return payout


async def assign_waiter_to_order(
    db: AsyncSession,
    order_id: UUID,
    payload: AssignWaiterRequest,
    request: Request | None = None,
    actor_user=None,
) -> Order:
    order = await db.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada",
        )

    user = await db.get(User, payload.waiter_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El usuario indicado no es válido",
        )

    if user.role not in (
        UserRole.MESERO,
        UserRole.ADMIN,
        UserRole.MANAGER,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El usuario indicado no puede ser mesero responsable",
        )

    order.waiter_id = user.id

    await db.commit()

    await audit(
        db,
        action="order.waiter_assigned",
        resource="order",
        resource_id=order.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={"waiter_id": str(user.id)},
    )

    return order


async def create_survey(
    db: AsyncSession,
    order_id: UUID,
    payload: SurveyCreateRequest,
    request: Request | None = None,
) -> Survey:
    order = await db.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada",
        )

    if order.status == OrderStatus.ENCUESTADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La orden ya fue encuestada",
        )

    if order.status != OrderStatus.PAGADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La orden debe estar pagada para responder la encuesta",
        )

    if order.order_type == OrderType.MESA:
        if not payload.codigo_qr:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El código QR es obligatorio para encuestas de mesa",
            )

        table = await _get_table_by_qr(db, payload.codigo_qr)

        if order.table_id != table.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden no encontrada para la mesa indicada",
            )

    elif order.order_type == OrderType.DOMICILIO:
        if not payload.telefono:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El teléfono es obligatorio para encuestas de domicilio",
            )

        delivery = await db.scalar(
            select(Delivery).where(Delivery.order_id == order.id)
        )

        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domicilio no encontrado",
            )

        if (
            delivery.customer_phone.replace(" ", "")
            != payload.telefono.replace(" ", "")
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden no encontrada para el teléfono indicado",
            )

    survey = Survey(
        order_id=order.id,
        food_score=payload.food_score,
        service_score=payload.service_score,
        general_score=payload.general_score,
        comment=payload.comment,
    )

    order.status = OrderStatus.ENCUESTADA

    db.add(survey)
    await db.flush()

    register_event(
        order=order,
        action="survey.created",
        actor_user=None,
        actor_role="CLIENTE",
        detail={
            "survey_id": str(survey.id),
            "general_score": survey.general_score,
        },
    )

    await db.commit()

    await audit(
        db,
        action="survey.created",
        resource="survey",
        resource_id=survey.id,
        request=request,
        detail={
            "order_id": str(order.id),
            "general_score": survey.general_score,
        },
    )

    return survey
