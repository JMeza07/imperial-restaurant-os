import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.invoice import Invoice
from app.models.order import Order
from app.services.invoice_service import generate_invoice_pdf_bytes, get_or_create_invoice_for_order
from app.services.order_service import _get_order_by_id, _get_table_by_qr


router = APIRouter()
admin_router = APIRouter()


@router.get(
    "/ordenes/{order_id}/factura",
    summary="Obtener factura de venta de la orden (Pública para el cliente por QR)",
)
async def get_order_invoice_public(
    order_id: UUID,
    codigo_qr: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    order = await _get_order_by_id(db, order_id)
    if codigo_qr:
        table = await _get_table_by_qr(db, codigo_qr)
        if order.table_id != table.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden no encontrada para la mesa",
            )

    invoice = await get_or_create_invoice_for_order(db, order)
    return {
        "id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "order_id": str(invoice.order_id),
        "table_number": invoice.table_number,
        "customer_name": invoice.customer_name,
        "customer_phone": invoice.customer_phone,
        "subtotal": float(invoice.subtotal),
        "tax_amount": float(invoice.tax_amount),
        "tip_amount": float(invoice.tip_amount),
        "delivery_fee": float(invoice.delivery_fee),
        "discount_amount": float(invoice.discount_amount),
        "total": float(invoice.total),
        "payment_method": invoice.payment_method,
        "items": invoice.items_snapshot,
        "restaurant": invoice.restaurant_snapshot,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
    }


@router.get(
    "/ordenes/{order_id}/factura/pdf",
    summary="Descargar factura de venta en PDF",
)
async def download_invoice_pdf_public(
    order_id: UUID,
    codigo_qr: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    order = await _get_order_by_id(db, order_id)
    if codigo_qr:
        table = await _get_table_by_qr(db, codigo_qr)
        if order.table_id != table.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden no encontrada para la mesa",
            )

    invoice = await get_or_create_invoice_for_order(db, order)

    # Si el archivo físico existe, servirlo directamente
    if invoice.pdf_path and os.path.exists(invoice.pdf_path):
        return FileResponse(
            invoice.pdf_path,
            media_type="application/pdf",
            filename=f"Factura_{invoice.invoice_number}.pdf",
        )

    # De lo contrario, generar los bytes al vuelo
    pdf_bytes = generate_invoice_pdf_bytes(invoice)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="Factura_{invoice.invoice_number}.pdf"'
        },
    )


@admin_router.get(
    "/facturas",
    summary="Listar facturas almacenadas en el sistema (Admin)",
)
async def list_invoices_admin(
    limit: int = 50,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    res = await db.scalars(
        select(Invoice).order_by(Invoice.created_at.desc()).limit(limit)
    )
    invoices = res.all()
    return [
        {
            "id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "order_id": str(inv.order_id),
            "table_number": inv.table_number,
            "customer_name": inv.customer_name,
            "customer_phone": inv.customer_phone,
            "total": float(inv.total),
            "payment_method": inv.payment_method,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in invoices
    ]
