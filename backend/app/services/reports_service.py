from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import (
    CommissionEventStatus,
    DeliveryStatus,
    OrderItemStatus,
    OrderStatus,
    PaymentStatus,
    StockMovementDirection,
    StockMovementType,
)
from app.models.catalog import Category, Dish, Ingredient
from app.models.commissions import CommissionEvent, CommissionPayout
from app.models.delivery import Delivery
from app.models.inventory import StockItem, StockMovement
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.commissions import Survey
from app.models.turnos import Employee


def get_date_range(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> tuple[datetime, datetime, date, date]:
    today = date.today()

    if date_from is None:
        date_from = today - timedelta(days=29)

    if date_to is None:
        date_to = today

    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_to debe ser mayor o igual que date_from",
        )

    start_dt = datetime.combine(
        date_from,
        time.min,
        tzinfo=timezone.utc,
    )

    end_dt = datetime.combine(
        date_to,
        time.max,
        tzinfo=timezone.utc,
    )

    return start_dt, end_dt, date_from, date_to


async def get_report_summary(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    branch_id: Optional[UUID] = None,
) -> dict:
    start_dt, end_dt, normalized_from, normalized_to = get_date_range(
        date_from,
        date_to,
    )

    sales_query = select(
        func.count(Order.id).label("paid_orders_count"),
        func.coalesce(func.sum(Order.total), 0).label("total_sales"),
        func.coalesce(func.avg(Order.total), 0).label("average_ticket"),
    ).where(
        Order.status.in_(
            [
                OrderStatus.PAGADA,
                OrderStatus.ENCUESTADA,
            ]
        ),
        Order.paid_at.is_not(None),
        Order.paid_at >= start_dt,
        Order.paid_at <= end_dt,
    )

    if branch_id:
        sales_query = sales_query.where(Order.branch_id == branch_id)

    sales_row = (await db.execute(sales_query)).one()

    open_orders_query = select(func.count(Order.id)).where(
        Order.status == OrderStatus.ABIERTA
    )

    if branch_id:
        open_orders_query = open_orders_query.where(
            Order.branch_id == branch_id
        )

    open_orders_count = await db.scalar(open_orders_query) or 0

    pending_kitchen_query = (
        select(func.count(OrderItem.id))
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.status == OrderStatus.ABIERTA,
            OrderItem.status.in_(
                [
                    OrderItemStatus.RECIBIDO,
                    OrderItemStatus.EN_PREPARACION,
                ]
            ),
        )
    )

    if branch_id:
        pending_kitchen_query = pending_kitchen_query.where(
            Order.branch_id == branch_id
        )

    pending_kitchen_items = await db.scalar(pending_kitchen_query) or 0

    survey_query = (
        select(
            func.count(Survey.id).label("surveys_count"),
            func.avg(Survey.general_score).label("avg_general_score"),
        )
        .join(Order, Survey.order_id == Order.id)
        .where(
            Survey.created_at >= start_dt,
            Survey.created_at <= end_dt,
        )
    )

    if branch_id:
        survey_query = survey_query.where(Order.branch_id == branch_id)

    survey_row = (await db.execute(survey_query)).one()

    low_stock_query = select(func.count(StockItem.id)).where(
        StockItem.quantity <= StockItem.min_quantity
    )

    if branch_id:
        low_stock_query = low_stock_query.where(
            StockItem.branch_id == branch_id
        )

    low_stock_count = await db.scalar(low_stock_query) or 0

    return {
        "date_from": normalized_from,
        "date_to": normalized_to,
        "total_sales": Decimal(str(sales_row.total_sales or 0)),
        "paid_orders_count": int(sales_row.paid_orders_count or 0),
        "average_ticket": Decimal(str(sales_row.average_ticket or 0)),
        "open_orders_count": int(open_orders_count),
        "pending_kitchen_items": int(pending_kitchen_items),
        "surveys_count": int(survey_row.surveys_count or 0),
        "avg_general_score": float(survey_row.avg_general_score)
        if survey_row.avg_general_score is not None
        else None,
        "low_stock_count": int(low_stock_count),
    }


async def get_daily_sales(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    branch_id: Optional[UUID] = None,
) -> List[dict]:
    start_dt, end_dt, _, _ = get_date_range(date_from, date_to)

    query = (
        select(
            func.date(Order.paid_at).label("report_date"),
            func.count(Order.id).label("orders_count"),
            func.coalesce(func.sum(Order.subtotal), 0).label("subtotal"),
            func.coalesce(func.sum(Order.tax_amount), 0).label("tax_amount"),
            func.coalesce(func.sum(Order.tip_amount), 0).label("tip_amount"),
            func.coalesce(func.sum(Order.delivery_fee), 0).label("delivery_fee"),
            func.coalesce(func.sum(Order.discount_amount), 0).label("discount_amount"),
            func.coalesce(func.sum(Order.total), 0).label("total"),
            func.coalesce(func.sum(Order.total_paid), 0).label("total_paid"),
        )
        .where(
            Order.status.in_(
                [
                    OrderStatus.PAGADA,
                    OrderStatus.ENCUESTADA,
                ]
            ),
            Order.paid_at.is_not(None),
            Order.paid_at >= start_dt,
            Order.paid_at <= end_dt,
        )
        .group_by("report_date")
        .order_by("report_date")
    )

    if branch_id:
        query = query.where(Order.branch_id == branch_id)

    rows = (await db.execute(query)).all()

    return [
        {
            "report_date": row.report_date,
            "orders_count": int(row.orders_count or 0),
            "subtotal": Decimal(str(row.subtotal or 0)),
            "tax_amount": Decimal(str(row.tax_amount or 0)),
            "tip_amount": Decimal(str(row.tip_amount or 0)),
            "delivery_fee": Decimal(str(row.delivery_fee or 0)),
            "discount_amount": Decimal(str(row.discount_amount or 0)),
            "total": Decimal(str(row.total or 0)),
            "total_paid": Decimal(str(row.total_paid or 0)),
        }
        for row in rows
    ]


async def get_sales_by_category(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    branch_id: Optional[UUID] = None,
) -> List[dict]:
    start_dt, end_dt, _, _ = get_date_range(date_from, date_to)

    query = (
        select(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.count(func.distinct(Dish.id)).label("dishes_count"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity"),
            func.coalesce(func.sum(OrderItem.subtotal), 0).label("revenue"),
        )
        .join(Dish, OrderItem.dish_id == Dish.id)
        .join(Category, Dish.category_id == Category.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.status.in_(
                [
                    OrderStatus.PAGADA,
                    OrderStatus.ENCUESTADA,
                ]
            ),
            OrderItem.status != OrderItemStatus.CANCELADO,
            Order.paid_at.is_not(None),
            Order.paid_at >= start_dt,
            Order.paid_at <= end_dt,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(OrderItem.subtotal).desc())
    )

    if branch_id:
        query = query.where(Order.branch_id == branch_id)

    rows = (await db.execute(query)).all()

    return [
        {
            "category_id": row.category_id,
            "category_name": row.category_name,
            "dishes_count": int(row.dishes_count or 0),
            "quantity": int(row.quantity or 0),
            "revenue": Decimal(str(row.revenue or 0)),
        }
        for row in rows
    ]


async def get_top_dishes(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    branch_id: Optional[UUID] = None,
    limit: int = 20,
) -> List[dict]:
    start_dt, end_dt, _, _ = get_date_range(date_from, date_to)

    query = (
        select(
            Dish.id.label("dish_id"),
            Dish.name.label("dish_name"),
            Category.name.label("category_name"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity"),
            func.coalesce(func.sum(OrderItem.subtotal), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.dish_id == Dish.id)
        .join(Order, OrderItem.order_id == Order.id)
        .join(Category, Dish.category_id == Category.id, isouter=True)
        .where(
            Order.status.in_(
                [
                    OrderStatus.PAGADA,
                    OrderStatus.ENCUESTADA,
                ]
            ),
            OrderItem.status != OrderItemStatus.CANCELADO,
            Order.paid_at.is_not(None),
            Order.paid_at >= start_dt,
            Order.paid_at <= end_dt,
        )
        .group_by(Dish.id, Dish.name, Category.name)
        .order_by(func.sum(OrderItem.subtotal).desc())
        .limit(limit)
    )

    if branch_id:
        query = query.where(Order.branch_id == branch_id)

    rows = (await db.execute(query)).all()

    return [
        {
            "dish_id": row.dish_id,
            "dish_name": row.dish_name,
            "category_name": row.category_name,
            "quantity": int(row.quantity or 0),
            "revenue": Decimal(str(row.revenue or 0)),
        }
        for row in rows
    ]


async def get_sales_by_payment_method(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    branch_id: Optional[UUID] = None,
) -> List[dict]:
    start_dt, end_dt, _, _ = get_date_range(date_from, date_to)

    query = (
        select(
            Payment.payment_method.label("payment_method"),
            func.count(Payment.id).label("payments_count"),
            func.coalesce(func.sum(Payment.amount), 0).label("amount"),
        )
        .join(Order, Payment.order_id == Order.id)
        .where(
            Payment.status == PaymentStatus.APROBADO,
            Payment.created_at >= start_dt,
            Payment.created_at <= end_dt,
        )
        .group_by(Payment.payment_method)
        .order_by(func.sum(Payment.amount).desc())
    )

    if branch_id:
        query = query.where(Order.branch_id == branch_id)

    rows = (await db.execute(query)).all()

    return [
        {
            "payment_method": row.payment_method,
            "payments_count": int(row.payments_count or 0),
            "amount": Decimal(str(row.amount or 0)),
        }
        for row in rows
    ]


async def get_employee_performance(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    branch_id: Optional[UUID] = None,
) -> List[dict]:
    start_dt, end_dt, _, _ = get_date_range(date_from, date_to)

    employees = await db.scalars(
        select(Employee).options(selectinload(Employee.user))
    ).all()

    user_to_employee = {}

    result = {}

    for employee in employees:
        if not employee.user:
            continue

        user_to_employee[employee.user_id] = employee

        result[employee.id] = {
            "employee_id": employee.id,
            "full_name": employee.full_name,
            "role": employee.user.role.value if employee.user else None,
            "orders_count": 0,
            "items_prepared": 0,
            "deliveries_count": 0,
            "sales_total": Decimal("0"),
            "commissions_total": Decimal("0"),
        }

    user_ids = list(user_to_employee.keys())

    if user_ids:
        orders_query = (
            select(
                Order.waiter_id.label("user_id"),
                func.count(Order.id).label("orders_count"),
                func.coalesce(func.sum(Order.total), 0).label("sales_total"),
            )
            .where(
                Order.waiter_id.in_(user_ids),
                Order.status.in_(
                    [
                        OrderStatus.PAGADA,
                        OrderStatus.ENCUESTADA,
                    ]
                ),
                Order.paid_at >= start_dt,
                Order.paid_at <= end_dt,
            )
            .group_by(Order.waiter_id)
        )

        if branch_id:
            orders_query = orders_query.where(Order.branch_id == branch_id)

        for row in (await db.execute(orders_query)).all():
            employee = user_to_employee.get(row.user_id)

            if employee:
                result[employee.id]["orders_count"] += int(row.orders_count or 0)
                result[employee.id]["sales_total"] += Decimal(str(row.sales_total or 0))

        deliveries_query = (
            select(
                Delivery.assigned_domiciliario_id.label("user_id"),
                func.count(Delivery.id).label("deliveries_count"),
            )
            .where(
                Delivery.assigned_domiciliario_id.in_(user_ids),
                Delivery.status == DeliveryStatus.ENTREGADO,
                Delivery.delivered_at >= start_dt,
                Delivery.delivered_at <= end_dt,
            )
            .group_by(Delivery.assigned_domiciliario_id)
        )

        if branch_id:
            deliveries_query = deliveries_query.join(
                Order,
                Delivery.order_id == Order.id,
            ).where(Order.branch_id == branch_id)

        for row in (await db.execute(deliveries_query)).all():
            employee = user_to_employee.get(row.user_id)

            if employee:
                result[employee.id]["deliveries_count"] += int(row.deliveries_count or 0)

        prepared_query = (
            select(
                OrderItem.prepared_by_user_id.label("user_id"),
                func.count(OrderItem.id).label("items_count"),
            )
            .where(
                OrderItem.prepared_by_user_id.in_(user_ids),
                OrderItem.created_at >= start_dt,
                OrderItem.created_at <= end_dt,
            )
            .group_by(OrderItem.prepared_by_user_id)
        )

        if branch_id:
            prepared_query = prepared_query.join(
                Order,
                OrderItem.order_id == Order.id,
            ).where(Order.branch_id == branch_id)

        for row in (await db.execute(prepared_query)).all():
            employee = user_to_employee.get(row.user_id)

            if employee:
                result[employee.id]["items_prepared"] += int(row.items_count or 0)

    commissions_query = (
        select(
            CommissionEvent.employee_id.label("employee_id"),
            func.coalesce(func.sum(CommissionEvent.amount), 0).label("total_amount"),
        )
        .where(
            CommissionEvent.status != CommissionEventStatus.ANULADA,
            CommissionEvent.created_at >= start_dt,
            CommissionEvent.created_at <= end_dt,
        )
        .group_by(CommissionEvent.employee_id)
    )

    for row in (await db.execute(commissions_query)).all():
        if row.employee_id in result:
            result[row.employee_id]["commissions_total"] += Decimal(
                str(row.total_amount or 0)
            )

    return list(result.values())


async def get_survey_summary(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    branch_id: Optional[UUID] = None,
) -> dict:
    start_dt, end_dt, _, _ = get_date_range(date_from, date_to)

    query = (
        select(
            func.count(Survey.id).label("surveys_count"),
            func.avg(Survey.food_score).label("avg_food_score"),
            func.avg(Survey.service_score).label("avg_service_score"),
            func.avg(Survey.general_score).label("avg_general_score"),
        )
        .join(Order, Survey.order_id == Order.id)
        .where(
            Survey.created_at >= start_dt,
            Survey.created_at <= end_dt,
        )
    )

    if branch_id:
        query = query.where(Order.branch_id == branch_id)

    row = (await db.execute(query)).one()

    comments_query = (
        select(Survey)
        .join(Order, Survey.order_id == Order.id)
        .where(
            Survey.created_at >= start_dt,
            Survey.created_at <= end_dt,
            Survey.comment.is_not(None),
        )
        .order_by(Survey.created_at.desc())
        .limit(20)
    )

    if branch_id:
        comments_query = comments_query.where(Order.branch_id == branch_id)

    comments = (await db.scalars(comments_query)).all()

    return {
        "surveys_count": int(row.surveys_count or 0),
        "avg_food_score": float(row.avg_food_score) if row.avg_food_score else None,
        "avg_service_score": float(row.avg_service_score) if row.avg_service_score else None,
        "avg_general_score": float(row.avg_general_score) if row.avg_general_score else None,
        "comments": [
            {
                "comment": comment.comment,
                "general_score": comment.general_score,
                "created_at": comment.created_at,
            }
            for comment in comments
        ],
    }


async def get_commission_summary(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> List[dict]:
    start_dt, end_dt, _, _ = get_date_range(date_from, date_to)

    employees = await db.scalars(
        select(Employee).options(selectinload(Employee.user))
    ).all()

    result = {}

    for employee in employees:
        result[employee.id] = {
            "employee_id": employee.id,
            "full_name": employee.full_name,
            "role": employee.user.role.value if employee.user else None,
            "total_calculated": Decimal("0"),
            "total_approved": Decimal("0"),
            "total_paid": Decimal("0"),
        }

    events_query = (
        select(
            CommissionEvent.employee_id.label("employee_id"),
            CommissionEvent.status.label("status"),
            func.coalesce(func.sum(CommissionEvent.amount), 0).label("amount"),
        )
        .where(
            CommissionEvent.status != CommissionEventStatus.ANULADA,
            CommissionEvent.created_at >= start_dt,
            CommissionEvent.created_at <= end_dt,
        )
        .group_by(CommissionEvent.employee_id, CommissionEvent.status)
    )

    for row in (await db.execute(events_query)).all():
        if row.employee_id not in result:
            continue

        amount = Decimal(str(row.amount or 0))

        result[row.employee_id]["total_calculated"] += amount

        if row.status == CommissionEventStatus.APROBADA:
            result[row.employee_id]["total_approved"] += amount

    payouts_query = (
        select(
            CommissionPayout.employee_id.label("employee_id"),
            func.coalesce(func.sum(CommissionPayout.amount), 0).label("amount"),
        )
        .where(
            CommissionPayout.status == CommissionPayoutStatus.PAGADO,
            CommissionPayout.created_at >= start_dt,
            CommissionPayout.created_at <= end_dt,
        )
        .group_by(CommissionPayout.employee_id)
    )

    for row in (await db.execute(payouts_query)).all():
        if row.employee_id in result:
            result[row.employee_id]["total_paid"] += Decimal(str(row.amount or 0))

    return list(result.values())


async def get_cash_summary(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    branch_id: Optional[UUID] = None,
) -> List[dict]:
    return await get_sales_by_payment_method(
        db=db,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
    )


async def get_inventory_consumption(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    branch_id: Optional[UUID] = None,
) -> List[dict]:
    start_dt, end_dt, _, _ = get_date_range(date_from, date_to)

    purchased_quantity = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        StockMovement.direction == StockMovementDirection.IN.value,
                        StockMovement.movement_type == StockMovementType.COMPRA.value,
                    ),
                    StockMovement.quantity,
                ),
                else_=0,
            )
        ),
        0,
    ).label("purchased_quantity")

    sold_quantity = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        StockMovement.direction == StockMovementDirection.OUT.value,
                        StockMovement.movement_type == StockMovementType.VENTA.value,
                    ),
                    StockMovement.quantity,
                ),
                else_=0,
            )
        ),
        0,
    ).label("sold_quantity")

    waste_quantity = func.coalesce(
        func.sum(
            case(
                (
                    StockMovement.movement_type == StockMovementType.DESPERDICIO.value,
                    StockMovement.quantity,
                ),
                else_=0,
            )
        ),
        0,
    ).label("waste_quantity")

    adjustment_out_quantity = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        StockMovement.direction == StockMovementDirection.OUT.value,
                        StockMovement.movement_type == StockMovementType.AJUSTE_SALIDA.value,
                    ),
                    StockMovement.quantity,
                ),
                else_=0,
            )
        ),
        0,
    ).label("adjustment_out_quantity")

    query = (
        select(
            Ingredient.id.label("ingredient_id"),
            Ingredient.name.label("ingredient_name"),
            purchased_quantity,
            sold_quantity,
            waste_quantity,
            adjustment_out_quantity,
        )
        .join(StockMovement, StockMovement.ingredient_id == Ingredient.id)
        .where(
            StockMovement.created_at >= start_dt,
            StockMovement.created_at <= end_dt,
        )
        .group_by(Ingredient.id, Ingredient.name)
        .order_by(Ingredient.name.asc())
    )

    if branch_id:
        query = query.where(StockMovement.branch_id == branch_id)

    rows = (await db.execute(query)).all()

    return [
        {
            "ingredient_id": row.ingredient_id,
            "ingredient_name": row.ingredient_name,
            "purchased_quantity": Decimal(str(row.purchased_quantity or 0)),
            "sold_quantity": Decimal(str(row.sold_quantity or 0)),
            "waste_quantity": Decimal(str(row.waste_quantity or 0)),
            "adjustment_out_quantity": Decimal(str(row.adjustment_out_quantity or 0)),
        }
        for row in rows
    ]
