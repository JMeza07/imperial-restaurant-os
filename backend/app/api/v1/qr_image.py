import io

import qrcode
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.restaurant import Table
from app.models.user import User


router = APIRouter()


@router.get(
    "/admin/mesas/{table_id}/qr-image",
    summary="Generar imagen PNG del QR",
)
async def get_qr_image(
    table_id,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    table = await db.get(Table, table_id)

    if not table:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada",
        )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(table.qr_url)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={
            "Content-Disposition": (
                f'inline; filename="mesa-{table.number}.png"'
            ),
            "Cache-Control": "private, max-age=3600",
        },
    )
