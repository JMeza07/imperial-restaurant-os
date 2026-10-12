import os
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import Invoice
from app.models.order import Order
from app.models.restaurant import Restaurant


INVOICES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static", "invoices")
os.makedirs(INVOICES_DIR, exist_ok=True)


def format_currency(val: Any) -> str:
    try:
        num = float(val or 0)
        return f"${num:,.0f}".replace(",", ".")
    except Exception:
        return f"${val}"


async def get_or_create_invoice_for_order(
    db: AsyncSession,
    order: Order,
    payment_method: Optional[str] = None,
) -> Invoice:
    # 1. Verificar si ya existe factura registrada
    existing = await db.scalar(
        select(Invoice).where(Invoice.order_id == order.id)
    )
    if existing:
        return existing

    # 1.1 Asegurar que la orden tenga items, platos y modificaciones cargados
    from app.models.order import OrderItem
    fresh_order = await db.scalar(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.modifications),
            selectinload(Order.items).selectinload(OrderItem.dish),
            selectinload(Order.table),
        )
        .where(Order.id == order.id)
    )
    if fresh_order:
        order = fresh_order

    # 2. Obtener datos del restaurante
    restaurant = await db.scalar(select(Restaurant).limit(1))
    rest_data = {
        "name": restaurant.name if restaurant else "Restaurante Imperial",
        "legal_name": restaurant.legal_name if restaurant and restaurant.legal_name else "Restaurante Imperial S.A.S.",
        "nit": restaurant.nit if restaurant and restaurant.nit else "901.458.789-1",
        "address": restaurant.address if restaurant and restaurant.address else "Calle del Comercio # 14-25, Lorica, Córdoba",
        "phone": restaurant.phone if restaurant and restaurant.phone else "+57 (314) 555-0199",
        "email": restaurant.email if restaurant and restaurant.email else "facturacion@imperial.local",
    }

    # 3. Snapshot de platos consumidos
    items_snapshot = []
    for item in (order.items or []):
        mods = [
            f"{m.action.value if hasattr(m.action, 'value') else m.action}: {m.ingredient_name}"
            for m in (item.modifications or [])
        ]
        items_snapshot.append({
            "id": str(item.id),
            "dish_name": item.dish_name or "Plato Imperial",
            "quantity": item.quantity,
            "unit_price": float(item.unit_price or 0),
            "subtotal": float(item.subtotal or 0),
            "observations": item.observations,
            "modifications": mods,
        })

    # 4. Generar consecutivo fiscal de factura
    invoice_number = f"FAC-{datetime.now().strftime('%Y%m')}-{str(order.id)[:8].upper()}"

    invoice = Invoice(
        invoice_number=invoice_number,
        order_id=order.id,
        table_number=order.table_number,
        customer_name=order.customer_name or "Cliente General",
        customer_phone=order.customer_phone or "Consumidor Final",
        subtotal=order.subtotal or Decimal("0"),
        tax_amount=order.tax_amount or Decimal("0"),
        tip_amount=order.tip_amount or Decimal("0"),
        delivery_fee=order.delivery_fee or Decimal("0"),
        discount_amount=order.discount_amount or Decimal("0"),
        total=order.total or order.subtotal or Decimal("0"),
        payment_method=payment_method or "EFECTIVO",
        items_snapshot=items_snapshot,
        restaurant_snapshot=rest_data,
    )

    db.add(invoice)
    await db.flush()

    # 5. Generar y almacenar archivo PDF en disco
    pdf_filename = f"{invoice_number}.pdf"
    pdf_path = os.path.join(INVOICES_DIR, pdf_filename)
    try:
        generate_invoice_pdf_file(invoice, pdf_path)
        invoice.pdf_path = pdf_path
    except Exception as e:
        print(f"Error generando PDF de factura en disco: {e}")

    await db.commit()
    await db.refresh(invoice)
    return invoice


def generate_invoice_pdf_bytes(invoice: Invoice) -> bytes:
    buffer = BytesIO()
    _build_pdf_document(invoice, buffer)
    buffer.seek(0)
    return buffer.getvalue()


def generate_invoice_pdf_file(invoice: Invoice, output_path: str):
    with open(output_path, "wb") as f:
        _build_pdf_document(invoice, f)


def _build_pdf_document(invoice: Invoice, stream_target):
    doc = SimpleDocTemplate(
        stream_target,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
    )

    rest_info_style = ParagraphStyle(
        "RestInfo",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )

    inv_badge_style = ParagraphStyle(
        "InvBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        alignment=2,  # Right
        textColor=colors.HexColor("#0f172a"),
    )

    inv_sub_style = ParagraphStyle(
        "InvSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=2,
        textColor=colors.HexColor("#64748b"),
    )

    header_cell_style = ParagraphStyle(
        "HeaderCell",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white,
    )

    cell_style = ParagraphStyle(
        "BodyCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
    )

    cell_bold_style = ParagraphStyle(
        "BodyCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )

    cell_desc_style = ParagraphStyle(
        "DescCell",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#64748b"),
    )

    elements = []

    rest = invoice.restaurant_snapshot or {}
    rest_name = rest.get("name", "RESTAURANTE IMPERIAL")
    rest_legal = rest.get("legal_name", "Imperial Restaurant S.A.S.")
    rest_nit = rest.get("nit", "NIT: 901.458.789-1")
    rest_addr = rest.get("address", "Lorica, Córdoba")
    rest_phone = rest.get("phone", "+57 314 555-0199")

    # ENCABEZADO: Datos del Restaurante a la izquierda | Datos de Factura a la derecha
    left_header = [
        Paragraph(f"<b>{rest_name.upper()}</b>", title_style),
        Spacer(1, 4),
        Paragraph(f"{rest_legal}", rest_info_style),
        Paragraph(f"NIT: {rest_nit}", rest_info_style),
        Paragraph(f"Dirección: {rest_addr}", rest_info_style),
        Paragraph(f"Teléfono: {rest_phone}", rest_info_style),
    ]

    fecha_emision = invoice.created_at.strftime("%d/%m/%Y %H:%M") if invoice.created_at else datetime.now().strftime("%d/%m/%Y %H:%M")
    mesa_texto = f"Mesa #{invoice.table_number}" if invoice.table_number else "Servicio Directo"

    right_header = [
        Paragraph(f"FACTURA DE VENTA", inv_badge_style),
        Paragraph(f"<b>{invoice.invoice_number}</b>", inv_badge_style),
        Spacer(1, 4),
        Paragraph(f"Fecha: {fecha_emision}", inv_sub_style),
        Paragraph(f"Ubicación: <b>{mesa_texto}</b>", inv_sub_style),
        Paragraph(f"Medio de Pago: <b>{invoice.payment_method or 'EFECTIVO'}</b>", inv_sub_style),
        Paragraph(f"Estado: <font color='#10b981'><b>PAGADA / CANCELADA</b></font>", inv_sub_style),
    ]

    header_table = Table([[left_header, right_header]], colWidths=[3.8 * inch, 3.6 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 14))

    # BARRA DE CLIENTE
    client_box = [
        [
            Paragraph(f"<b>CLIENTE:</b> {invoice.customer_name or 'Consumidor Final'}", cell_style),
            Paragraph(f"<b>DOC / TEL:</b> {invoice.customer_phone or 'N/A'}", cell_style),
        ]
    ]
    client_table = Table(client_box, colWidths=[4.2 * inch, 3.2 * inch])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 14))

    # TABLA DE CONSUMO / PLATOS
    item_rows = [
        [
            Paragraph("CANT", header_cell_style),
            Paragraph("DESCRIPCIÓN DEL PLATO / CONSUMO", header_cell_style),
            Paragraph("VALOR UNIT.", header_cell_style),
            Paragraph("TOTAL", header_cell_style),
        ]
    ]

    for it in (invoice.items_snapshot or []):
        mods_text = ""
        if it.get("modifications"):
            mods_text = "<br/>• " + "<br/>• ".join(it["modifications"])
        if it.get("observations"):
            mods_text += f"<br/><i>Nota: {it['observations']}</i>"

        desc_content = [
            Paragraph(f"<b>{it.get('dish_name')}</b>", cell_bold_style)
        ]
        if mods_text:
            desc_content.append(Paragraph(mods_text, cell_desc_style))

        item_rows.append([
            Paragraph(str(it.get("quantity", 1)), cell_style),
            desc_content,
            Paragraph(format_currency(it.get("unit_price", 0)), cell_style),
            Paragraph(format_currency(it.get("subtotal", 0)), cell_bold_style),
        ])

    table_items = Table(item_rows, colWidths=[0.8 * inch, 4.4 * inch, 1.1 * inch, 1.1 * inch])
    table_items.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    elements.append(table_items)
    elements.append(Spacer(1, 12))

    # TOTALES FINANCIEROS LIQUIDADOS
    totales_data = [
        [Paragraph("Subtotal Consumo:", cell_style), Paragraph(format_currency(invoice.subtotal), cell_bold_style)],
    ]
    if float(invoice.tax_amount or 0) > 0:
        totales_data.append([Paragraph("Impuesto al Consumo (8%):", cell_style), Paragraph(format_currency(invoice.tax_amount), cell_style)])
    if float(invoice.tip_amount or 0) > 0:
        totales_data.append([Paragraph("Propina Voluntaria del Servicio:", cell_style), Paragraph(format_currency(invoice.tip_amount), cell_style)])
    if float(invoice.delivery_fee or 0) > 0:
        totales_data.append([Paragraph("Tarifa de Domicilio:", cell_style), Paragraph(format_currency(invoice.delivery_fee), cell_style)])
    if float(invoice.discount_amount or 0) > 0:
        totales_data.append([Paragraph("Descuento Aplicado:", cell_style), Paragraph(f"-{format_currency(invoice.discount_amount)}", cell_style)])

    total_style_big = ParagraphStyle(
        "TotalBig",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        alignment=2,
        textColor=colors.HexColor("#0f172a"),
    )

    totales_data.append([
        Paragraph("<b>TOTAL A PAGAR:</b>", total_style_big),
        Paragraph(f"<b>{format_currency(invoice.total)}</b>", total_style_big),
    ])

    totales_table = Table(totales_data, colWidths=[2.2 * inch, 1.4 * inch])
    totales_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor("#0f172a")),
    ]))

    # Poner totales alineados a la derecha
    align_table = Table([[Spacer(1, 1), totales_table]], colWidths=[3.8 * inch, 3.6 * inch])
    align_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(align_table)
    elements.append(Spacer(1, 24))

    # PIE DE PÁGINA FISCAL
    footer_text = (
        "Esta factura de venta se expide de conformidad con los requisitos fiscales vigentes.<br/>"
        "¡Gracias por su visita al Restaurante Imperial! Conserve esta factura para cualquier reclamo."
    )
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=10, spaceAfter=8))
    elements.append(Paragraph(footer_text, ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        alignment=1,  # Center
        textColor=colors.HexColor("#64748b"),
    )))

    doc.build(elements)
