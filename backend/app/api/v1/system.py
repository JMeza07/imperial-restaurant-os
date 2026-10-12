from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User


admin_router = APIRouter()


@admin_router.get(
    "/system/health",
    summary="Estado interno del sistema",
)
async def system_health(
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text

    await db.execute(text("SELECT 1"))

    from app.core.redis import redis_client

    await redis_client.ping()

    users_count = await db.scalar(select(func.count(User.id)))

    return {
        "status": "ok",
        "database": "ok",
        "redis": "ok",
        "users_count": users_count,
    }


@admin_router.get(
    "/system/audit-stats",
    summary="Estadísticas de auditoría",
)
async def audit_stats(
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.AUDITOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        select(
            AuditLog.action,
            func.count(AuditLog.id),
        )
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
        .limit(20)
    )

    return {
        "top_actions": [
            {
                "action": row.action,
                "count": int(row.count),
            }
            for row in rows.all()
        ],
    }
