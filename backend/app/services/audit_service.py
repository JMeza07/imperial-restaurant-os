from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_value(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, UUID):
        return str(value)

    return value


async def audit(
    db: AsyncSession,
    *,
    action: str,
    resource: str,
    resource_id: Optional[UUID | str] = None,
    user_id: Optional[UUID] = None,
    request: Optional[Request] = None,
    detail: Optional[dict[str, Any]] = None,
) -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
        detail=_sanitize_value(detail),
    )

    db.add(log)
    await db.commit()
