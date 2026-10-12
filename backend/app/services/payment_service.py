from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import (
    CashSessionStatus,
    OrderItemStatus,
    OrderStatus,
    OrderType,
    PaymentMethod,
    PaymentStatus,
    TableStatus,
)
from app.models.order import Order
from app.models.payment import CashSession, Payment
from app.models.restaurant import Branch, Table
from app.schemas.payment import (
    CashSessionCloseRequest,
    CashSessionOpenRequest,
    CloseOrderRequest,
    PaymentCreateRequest,
)
from app.services.audit_service import audit
from app.services.invoice_service import get_or_create_invoice_for_order
from app.services.order_service import _get_table_by_qr, order_options, register_event
from app.services.restaurant_service import get_default_restaurant


def round_money(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def can_close_order(item_statuses: Iterable[OrderItemStatus]) -> bool:
    """
    RN-08:
    El administrador solo puede cerrar una orden si todos sus platos
    están en estado ENTREGADO o CANCELADO.
    """

    statuses = list(item_statuses)

    if not statuses:
        return False

    return all(
        item_status in (
            OrderItemStatus.ENTREGADO,
            OrderItemStatus.CANCELADO,
        )
        for item_status in statuses
    )


def calculate_order_totals(
    subtotal: Decimal,
    tax_rate: Decimal,
    tip_rate: Optional[Decimal] = None,
    tip_amount: Optional[Decimal] = None,
    delivery_fee: Decimal = Decimal("0"),
    discount_amount: Decimal = Decimal("0"),
) -> dict:
    """
    RN-09:
    Total = subtotal + impuesto + propina + costo de envío - descuentos.
    """

    if subtotal < 0:
        raise ValueError("El subtotal no puede ser negativo")

    if tax_rate < 0 or tax_rate > 1:
        raise ValueError("La tasa de impuesto debe estar entre 0 y 1")

    if tip_rate is not None and tip_amount is not None:
        raise ValueError("No se puede indicar tip_rate y tip_amount al mismo tiempo")

    if tip_rate is not None and (tip_rate < 0 or tip_rate > 1):
        raise ValueError("La tasa de propina debe estar entre 0 y 1")

    if tip_amount is not None and tip_amount < 0:
        raise ValueError("El valor de propina no puede ser negativo")

    if delivery_fee < 0:
        raise ValueError("El costo de envío no puede ser negativo")

    if discount_amount < 0:
        raise ValueError("El descuento no puede ser negativo")

    tax_amount = round_money(subtotal * tax_rate)

    if tip_amount is not None:
        tip_value = round_money(tip_amount)
    elif tip_rate is not None:
        tip_value = round_money(subtotal * tip_rate)
    else:
        tip_value = Decimal("0")

    delivery_value = round_money(delivery_fee or Decimal("0"))
    discount_value = round_money(discount_amount or Decimal("0"))

    total = round_money(
        subtotal + tax_amount + tip_value + delivery_value - discount_value
    )

    if total < 0:
        total = Decimal("0")

    return {
        "subtotal": round_money(subtotal),
        "tax_amount": tax_amount,
        "tip_amount": tip_value,
        "delivery_fee": delivery_value,
        "discount_amount": discount_value,
        "total": total,
    }


async def _get_order_by_id(
    db: AsyncSession,
    order_id: UUID,
) -> Order:
    order = await db.scalar(
        select(Order)
        .options(*order_options())
        .where(Order.id == order_id)
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada",
        )

    return order


async def _get_payment_by_id(
    db: AsyncSession,
    payment_id: UUID,
) -> Payment:
    payment = await db.scalar(
        select(Payment)
        .options(selectinload(Payment.order))
        .where(Payment.id == payment_id)
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado",
        )

    return payment


async def close_order(
    db: AsyncSession,
    order_id: UUID,
    payload: CloseOrderRequest,
    request: Request | None = None,
    actor_user=None,
) -> Order:
    order = await _get_order_by_id(db, order_id)

    if order.status != OrderStatus.ABIERTA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La orden no puede cerrarse porque no está abierta",
        )

    if getattr(payload, "auto_deliver_pending", True):
        for item in order.items:
            if item.status not in (
                OrderItemStatus.ENTREGADO,
                OrderItemStatus.CANCELADO,
            ):
                item.status = OrderItemStatus.ENTREGADO
                item.delivered_at = datetime.now(timezone.utc)
        await db.flush()

    item_statuses = [item.status for item in order.items]

    # RN-08: No cerrar con platos pendientes.
    if not can_close_order(item_statuses):
        pending_items = [
            {
                "item_id": str(item.id),
                "dish": item.dish_name,
                "status": item.status.value,
            }
            for item in order.items
            if item.status not in (
                OrderItemStatus.ENTREGADO,
                OrderItemStatus.CANCELADO,
            )
        ]

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "No se puede cerrar la cuenta porque hay platos pendientes",
                "pending_items": pending_items,
            },
        )

    subtotal = sum(
        (
            item.subtotal
            for item in order.items
            if item.status != OrderItemStatus.CANCELADO
        ),
        Decimal("0"),
    )

    restaurant = await get_default_restaurant(db)

    tax_rate = (
        payload.tax_rate
        if payload.tax_rate is not None
        else restaurant.default_tax_rate
    )

    if order.order_type == OrderType.DOMICILIO:
        delivery_fee = (
            payload.delivery_fee
            if payload.delivery_fee is not None
            else order.delivery_fee
        )
    else:
        delivery_fee = Decimal("0")

    try:
        totals = calculate_order_totals(
            subtotal=subtotal,
            tax_rate=tax_rate,
            tip_rate=payload.tip_rate,
            tip_amount=payload.tip_amount,
            delivery_fee=delivery_fee,
            discount_amount=order.discount_amount,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )

    now = datetime.now(timezone.utc)

    order.subtotal = totals["subtotal"]
    order.tax_amount = totals["tax_amount"]
    order.tip_amount = totals["tip_amount"]
    order.delivery_fee = totals["delivery_fee"]
    order.discount_amount = totals["discount_amount"]
    order.total = totals["total"]
    order.closed_at = now

    if order.total == Decimal("0"):
        order.status = OrderStatus.PAGADA
        order.paid_at = now
    else:
        order.status = OrderStatus.CERRADA

    await db.flush()

    register_event(
        order=order,
        action="order.closed",
        actor_user=actor_user,
        actor_role=actor_user.role.value if actor_user else None,
        detail={
            "subtotal": str(order.subtotal),
            "tax_amount": str(order.tax_amount),
            "tip_amount": str(order.tip_amount),
            "delivery_fee": str(order.delivery_fee),
            "discount_amount": str(order.discount_amount),
            "total": str(order.total),
        },
    )

    await db.commit()

    await audit(
        db,
        action="order.closed",
        resource="order",
        resource_id=order.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "total": str(order.total),
            "status": order.status.value,
        },
    )

    return await _get_order_by_id(db, order.id)


async def _get_order_ready_for_payment(
    db: AsyncSession,
    order_id: UUID,
    codigo_qr: Optional[str] = None,
    require_qr: bool = False,
) -> Order:
    order = await _get_order_by_id(db, order_id)

    if require_qr:
        if not codigo_qr:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El código QR es obligatorio para pagar una orden de mesa",
            )

        table = await _get_table_by_qr(db, codigo_qr)

        if order.table_id != table.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden no encontrada para la mesa indicada",
            )

    if order.status == OrderStatus.PAGADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La orden ya está pagada",
        )

    if order.status != OrderStatus.CERRADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La orden debe estar cerrada para registrar pagos",
        )

    return order


async def _register_payment(
    db: AsyncSession,
    order: Order,
    payload: PaymentCreateRequest,
    request: Request | None = None,
    actor_user=None,
) -> Payment:
    amount = round_money(payload.amount)

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El monto del pago debe ser mayor que cero",
        )

    if (not order.total or order.total == Decimal("0")) and order.subtotal > Decimal("0"):
        order.total = order.subtotal

    saldo = order.saldo_pendiente

    if saldo < 0:
        saldo = Decimal("0")

    # RN-10: No se acepta un pago mayor que el saldo pendiente.
    if amount > saldo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El monto del pago supera el saldo pendiente de {saldo}",
        )

    now = datetime.now(timezone.utc)

    reference = payload.reference

    if not reference:
        reference = f"{payload.payment_method.value}-{uuid4().hex[:8].upper()}"

    payment = Payment(
        order_id=order.id,
        payment_method=payload.payment_method,
        status=PaymentStatus.APROBADO,
        amount=amount,
        reference=reference,
        note=payload.note,
        registered_by_user_id=actor_user.id if actor_user else None,
        approved_at=now,
    )

    if order.branch_id:
        cash_session = await db.scalar(
            select(CashSession).where(
                CashSession.branch_id == order.branch_id,
                CashSession.status == CashSessionStatus.ABIERTA,
            )
        )

        if cash_session:
            payment.cash_session_id = cash_session.id

    order.total_paid = round_money(order.total_paid + amount)

    # RN-10: La orden pasa a PAGADA cuando la suma aprobada cubre el total.
    target_total = order.total if (order.total and order.total > Decimal("0")) else order.subtotal
    if order.total_paid >= target_total:
        order.status = OrderStatus.PAGADA
        order.paid_at = now

        # Liberar la mesa para dejarla en cero disponible para el próximo cliente
        if order.table_id:
            table = await db.get(Table, order.table_id)
            if table:
                table.status = TableStatus.LIBRE

        # Generar y almacenar factura legal en base de datos y archivo PDF
        try:
            await get_or_create_invoice_for_order(
                db=db,
                order=order,
                payment_method=payment.payment_method.value if hasattr(payment.payment_method, "value") else str(payment.payment_method),
            )
        except Exception as inv_err:
            print(f"Error generando factura para orden {order.id}: {inv_err}")

    db.add(payment)
    await db.flush()

    register_event(
        order=order,
        action="payment.registered",
        actor_user=actor_user,
        actor_role=actor_user.role.value if actor_user else None,
        detail={
            "payment_id": str(payment.id),
            "payment_method": payment.payment_method.value,
            "amount": str(payment.amount),
            "reference": payment.reference,
            "total_paid": str(order.total_paid),
            "order_status": order.status.value,
        },
    )

    await db.commit()

    await audit(
        db,
        action="payment.registered",
        resource="payment",
        resource_id=payment.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "order_id": str(order.id),
            "amount": str(payment.amount),
            "payment_method": payment.payment_method.value,
        },
    )

    return await _get_payment_by_id(db, payment.id)


async def register_payment_public(
    db: AsyncSession,
    order_id: UUID,
    payload: PaymentCreateRequest,
    request: Request | None = None,
) -> Payment:
    order = await _get_order_by_id(db, order_id)

    if order.order_type != OrderType.MESA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Por ahora el pago público solo está habilitado para órdenes de mesa",
        )

    # Si la orden aún está ABIERTA, prepararla automáticamente para el pago del cliente:
    if order.status == OrderStatus.ABIERTA:
        for it in (order.items or []):
            if it.status not in (OrderItemStatus.ENTREGADO, OrderItemStatus.CANCELADO):
                it.status = OrderItemStatus.ENTREGADO
                it.delivered_at = datetime.now(timezone.utc)
        await db.flush()

        await close_order(
            db=db,
            order_id=order.id,
            payload=CloseOrderRequest(),
            request=request,
            actor_user=None,
        )
        order = await _get_order_by_id(db, order_id)

    order = await _get_order_ready_for_payment(
        db=db,
        order_id=order_id,
        codigo_qr=payload.codigo_qr,
        require_qr=True,
    )

    return await _register_payment(
        db=db,
        order=order,
        payload=payload,
        request=request,
        actor_user=None,
    )


async def register_payment_admin(
    db: AsyncSession,
    order_id: UUID,
    payload: PaymentCreateRequest,
    request: Request | None = None,
    actor_user=None,
) -> Payment:
    order = await _get_order_by_id(db, order_id)

    # Si la orden aún está ABIERTA, prepararla automáticamente para el cobro del administrador:
    if order.status == OrderStatus.ABIERTA:
        for it in (order.items or []):
            if it.status not in (OrderItemStatus.ENTREGADO, OrderItemStatus.CANCELADO):
                it.status = OrderItemStatus.ENTREGADO
                it.delivered_at = datetime.now(timezone.utc)
        await db.flush()

        await close_order(
            db=db,
            order_id=order.id,
            payload=CloseOrderRequest(),
            request=request,
            actor_user=actor_user,
        )
        order = await _get_order_by_id(db, order_id)

    order = await _get_order_ready_for_payment(
        db=db,
        order_id=order_id,
        require_qr=False,
    )

    return await _register_payment(
        db=db,
        order=order,
        payload=payload,
        request=request,
        actor_user=actor_user,
    )


async def list_order_payments(
    db: AsyncSession,
    order_id: UUID,
) -> List[Payment]:
    query = (
        select(Payment)
        .options(selectinload(Payment.order))
        .where(Payment.order_id == order_id)
        .order_by(Payment.created_at.asc())
    )

    return (await db.scalars(query)).all()


async def _get_default_branch(db: AsyncSession) -> Branch:
    branch = await db.scalar(
        select(Branch)
        .where(Branch.is_active.is_(True))
        .order_by(Branch.created_at.asc())
    )

    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una sucursal activa",
        )

    return branch


async def open_cash_session(
    db: AsyncSession,
    payload: CashSessionOpenRequest,
    request: Request | None = None,
    actor_user=None,
) -> CashSession:
    branch_id = payload.branch_id

    if not branch_id:
        branch = await _get_default_branch(db)
        branch_id = branch.id

    existing_session = await db.scalar(
        select(CashSession).where(
            CashSession.branch_id == branch_id,
            CashSession.status == CashSessionStatus.ABIERTA,
        )
    )

    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una caja abierta para esta sucursal",
        )

    session = CashSession(
        branch_id=branch_id,
        opened_by_user_id=actor_user.id if actor_user else None,
        status=CashSessionStatus.ABIERTA,
        opening_amount=round_money(payload.opening_amount),
        notes=payload.notes,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    await audit(
        db,
        action="cash_session.opened",
        resource="cash_session",
        resource_id=session.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "branch_id": str(branch_id),
            "opening_amount": str(session.opening_amount),
        },
    )

    return session


async def get_open_cash_session(
    db: AsyncSession,
    branch_id: Optional[UUID] = None,
) -> CashSession:
    if not branch_id:
        branch = await _get_default_branch(db)
        branch_id = branch.id

    session = await db.scalar(
        select(CashSession).where(
            CashSession.branch_id == branch_id,
            CashSession.status == CashSessionStatus.ABIERTA,
        )
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una caja abierta para esta sucursal",
        )

    return session


async def close_cash_session(
    db: AsyncSession,
    session_id: UUID,
    payload: CashSessionCloseRequest,
    request: Request | None = None,
    actor_user=None,
) -> CashSession:
    session = await db.get(CashSession, session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión de caja no encontrada",
        )

    if session.status != CashSessionStatus.ABIERTA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La sesión de caja ya está cerrada",
        )

    cash_payments_total = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.cash_session_id == session.id,
            Payment.status == PaymentStatus.APROBADO,
            Payment.payment_method == PaymentMethod.EFECTIVO,
        )
    )

    expected_amount = round_money(
        session.opening_amount + Decimal(str(cash_payments_total))
    )

    now = datetime.now(timezone.utc)

    session.status = CashSessionStatus.CERRADA
    session.closed_by_user_id = actor_user.id if actor_user else None
    session.closed_at = now
    session.expected_amount = expected_amount
    session.closing_amount = round_money(payload.closing_amount)

    if payload.notes:
        session.notes = payload.notes

    await db.commit()
    await db.refresh(session)

    await audit(
        db,
        action="cash_session.closed",
        resource="cash_session",
        resource_id=session.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "expected_amount": str(session.expected_amount),
            "closing_amount": str(session.closing_amount),
        },
    )

    return session
