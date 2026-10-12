from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import ShiftEventType, ShiftStatus, UserRole
from app.models.restaurant import Branch, Table
from app.models.turnos import (
    ClockEvent,
    Employee,
    Shift,
    ShiftAssignment,
    ShiftBreak,
    ShiftTemplate,
)
from app.models.user import User
from app.schemas.turnos import (
    EmployeeCreate,
    EmployeeUpdate,
    GenerateShiftsRequest,
    ShiftAssignmentUpdate,
    ShiftCreate,
    ShiftTemplateCreate,
    ShiftTemplateUpdate,
    ShiftUpdate,
)
from app.services.audit_service import audit


SHIFT_EARLY_MINUTES = 30
SHIFT_LATE_MINUTES = 30

ADMIN_SHIFT_ROLES = (
    UserRole.ADMIN,
    UserRole.MANAGER,
    UserRole.RRHH,
)


def can_transition_shift(
    current_status: ShiftStatus,
    target_status: ShiftStatus,
) -> bool:
    if current_status == ShiftStatus.PROGRAMADO:
        return target_status in (
            ShiftStatus.CONFIRMADO,
            ShiftStatus.AUSENTE,
            ShiftStatus.CANCELADO,
        )

    if current_status == ShiftStatus.CONFIRMADO:
        return target_status in (
            ShiftStatus.EN_TURNO,
            ShiftStatus.AUSENTE,
            ShiftStatus.CANCELADO,
        )

    if current_status == ShiftStatus.EN_TURNO:
        return target_status in (
            ShiftStatus.EN_DESCANSO,
            ShiftStatus.FINALIZADO,
        )

    if current_status == ShiftStatus.EN_DESCANSO:
        return target_status == ShiftStatus.EN_TURNO

    return False


def employee_options():
    return [
        selectinload(Employee.user),
        selectinload(Employee.branch),
    ]


def shift_options():
    return [
        selectinload(Shift.employee).selectinload(Employee.user),
        selectinload(Shift.branch),
        selectinload(Shift.breaks),
        selectinload(Shift.clock_events),
        selectinload(Shift.assignments).selectinload(ShiftAssignment.table),
    ]


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value


async def _get_employee_by_id(
    db: AsyncSession,
    employee_id: UUID,
) -> Employee:
    employee = await db.scalar(
        select(Employee)
        .options(*employee_options())
        .where(Employee.id == employee_id)
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado",
        )

    return employee


async def _get_employee_by_user_id(
    db: AsyncSession,
    user_id: UUID,
) -> Employee:
    employee = await db.scalar(
        select(Employee)
        .options(*employee_options())
        .where(Employee.user_id == user_id)
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no tiene perfil de empleado",
        )

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El empleado está inactivo",
        )

    return employee


async def list_employees(
    db: AsyncSession,
    branch_id: Optional[UUID] = None,
    include_inactive: bool = False,
) -> List[Employee]:
    query = select(Employee).options(*employee_options())

    if branch_id:
        query = query.where(Employee.branch_id == branch_id)

    if not include_inactive:
        query = query.where(Employee.is_active.is_(True))

    query = query.order_by(Employee.created_at.asc())

    return (await db.scalars(query)).all()


async def get_employee(
    db: AsyncSession,
    employee_id: UUID,
) -> Employee:
    return await _get_employee_by_id(db, employee_id)


async def create_employee(
    db: AsyncSession,
    payload: EmployeeCreate,
    request: Request | None = None,
    actor_user=None,
) -> Employee:
    user = await db.get(User, payload.user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El usuario indicado no es válido",
        )

    existing_employee = await db.scalar(
        select(Employee).where(Employee.user_id == payload.user_id)
    )

    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya tiene un perfil de empleado",
        )

    existing_code = await db.scalar(
        select(Employee).where(Employee.employee_code == payload.employee_code)
    )

    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un empleado con este código",
        )

    if payload.document_number:
        existing_document = await db.scalar(
            select(Employee).where(
                Employee.document_number == payload.document_number
            )
        )

        if existing_document:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un empleado con este documento",
            )

    if payload.branch_id:
        branch = await db.get(Branch, payload.branch_id)

        if not branch or not branch.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La sucursal indicada no es válida",
            )

    employee = Employee(
        user_id=payload.user_id,
        branch_id=payload.branch_id,
        employee_code=payload.employee_code,
        document_number=payload.document_number,
        position=payload.position,
        hourly_wage=payload.hourly_wage,
        is_active=payload.is_active,
    )

    db.add(employee)
    await db.commit()
    await db.refresh(employee)

    await audit(
        db,
        action="employee.created",
        resource="employee",
        resource_id=employee.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "employee_code": employee.employee_code,
            "user_id": str(employee.user_id),
        },
    )

    return await _get_employee_by_id(db, employee.id)


async def update_employee(
    db: AsyncSession,
    employee_id: UUID,
    payload: EmployeeUpdate,
    request: Request | None = None,
    actor_user=None,
) -> Employee:
    employee = await _get_employee_by_id(db, employee_id)

    changes = {}
    data = payload.model_dump(exclude_unset=True)

    if payload.employee_code is not None and payload.employee_code != employee.employee_code:
        existing_code = await db.scalar(
            select(Employee).where(
                Employee.employee_code == payload.employee_code,
                Employee.id != employee.id,
            )
        )

        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un empleado con este código",
            )

    if payload.document_number is not None and payload.document_number != employee.document_number:
        existing_document = await db.scalar(
            select(Employee).where(
                Employee.document_number == payload.document_number,
                Employee.id != employee.id,
            )
        )

        if existing_document:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un empleado con este documento",
            )

    for field, value in data.items():
        setattr(employee, field, value)
        changes[field] = value

    await db.commit()

    await audit(
        db,
        action="employee.updated",
        resource="employee",
        resource_id=employee.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail=changes,
    )

    return await _get_employee_by_id(db, employee.id)


async def list_shift_templates(
    db: AsyncSession,
    include_inactive: bool = False,
) -> List[ShiftTemplate]:
    query = select(ShiftTemplate).order_by(ShiftTemplate.name.asc())

    if not include_inactive:
        query = query.where(ShiftTemplate.is_active.is_(True))

    return (await db.scalars(query)).all()


async def create_shift_template(
    db: AsyncSession,
    payload: ShiftTemplateCreate,
    request: Request | None = None,
    actor_user=None,
) -> ShiftTemplate:
    if payload.branch_id:
        branch = await db.get(Branch, payload.branch_id)

        if not branch or not branch.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La sucursal indicada no es válida",
            )

    template = ShiftTemplate(
        branch_id=payload.branch_id,
        name=payload.name,
        start_time=payload.start_time,
        end_time=payload.end_time,
        weekdays=payload.weekdays,
        notes=payload.notes,
        is_active=payload.is_active,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    await audit(
        db,
        action="shift_template.created",
        resource="shift_template",
        resource_id=template.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={"name": template.name},
    )

    return template


async def update_shift_template(
    db: AsyncSession,
    template_id: UUID,
    payload: ShiftTemplateUpdate,
    request: Request | None = None,
    actor_user=None,
) -> ShiftTemplate:
    template = await db.get(ShiftTemplate, template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla de turno no encontrada",
        )

    changes = {}
    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(template, field, value)
        changes[field] = value

    await db.commit()
    await db.refresh(template)

    await audit(
        db,
        action="shift_template.updated",
        resource="shift_template",
        resource_id=template.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail=changes,
    )

    return template


async def _exists_shift_overlap(
    db: AsyncSession,
    employee_id: UUID,
    start: datetime,
    end: datetime,
    exclude_shift_id: Optional[UUID] = None,
) -> bool:
    query = select(Shift.id).where(
        Shift.employee_id == employee_id,
        Shift.status != ShiftStatus.CANCELADO,
        or_(
            and_(
                Shift.scheduled_start <= start,
                Shift.scheduled_end > start,
            ),
            and_(
                Shift.scheduled_start < end,
                Shift.scheduled_end >= end,
            ),
            and_(
                Shift.scheduled_start >= start,
                Shift.scheduled_end <= end,
            ),
        ),
    )

    if exclude_shift_id:
        query = query.where(Shift.id != exclude_shift_id)

    row = await db.scalar(query)

    return row is not None


async def create_shift(
    db: AsyncSession,
    payload: ShiftCreate,
    request: Request | None = None,
    actor_user=None,
) -> Shift:
    employee = await _get_employee_by_id(db, payload.employee_id)

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El empleado está inactivo",
        )

    branch_id = payload.branch_id or employee.branch_id

    if branch_id:
        branch = await db.get(Branch, branch_id)

        if not branch or not branch.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La sucursal indicada no es válida",
            )

    if payload.scheduled_end <= payload.scheduled_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La hora fin del turno debe ser mayor que la hora inicio",
        )

    if await _exists_shift_overlap(
        db=db,
        employee_id=employee.id,
        start=payload.scheduled_start,
        end=payload.scheduled_end,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El empleado ya tiene un turno que se cruza con este horario",
        )

    shift = Shift(
        employee_id=employee.id,
        branch_id=branch_id,
        status=ShiftStatus.PROGRAMADO,
        scheduled_start=payload.scheduled_start,
        scheduled_end=payload.scheduled_end,
        notes=payload.notes,
    )

    db.add(shift)
    await db.commit()

    await audit(
        db,
        action="shift.created",
        resource="shift",
        resource_id=shift.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "employee_id": str(employee.id),
            "scheduled_start": str(payload.scheduled_start),
            "scheduled_end": str(payload.scheduled_end),
        },
    )

    return await get_shift_admin(db, shift.id)


async def _get_shift_by_id(
    db: AsyncSession,
    shift_id: UUID,
) -> Shift:
    shift = await db.scalar(
        select(Shift)
        .options(*shift_options())
        .where(Shift.id == shift_id)
    )

    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno no encontrado",
        )

    return shift


async def get_shift_admin(
    db: AsyncSession,
    shift_id: UUID,
) -> Shift:
    return await _get_shift_by_id(db, shift_id)


async def list_shifts_admin(
    db: AsyncSession,
    employee_id: Optional[UUID] = None,
    branch_id: Optional[UUID] = None,
    shift_status: Optional[ShiftStatus] = None,
    date_from=None,
    date_to=None,
) -> List[Shift]:
    query = select(Shift).options(*shift_options())

    if employee_id:
        query = query.where(Shift.employee_id == employee_id)

    if branch_id:
        query = query.where(Shift.branch_id == branch_id)

    if shift_status:
        query = query.where(Shift.status == shift_status)

    if date_from:
        start = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
        query = query.where(Shift.scheduled_start >= start)

    if date_to:
        end = datetime.combine(date_to, datetime.max.time(), tzinfo=timezone.utc)
        query = query.where(Shift.scheduled_start <= end)

    query = query.order_by(Shift.scheduled_start.asc())

    return (await db.scalars(query)).all()


async def update_shift(
    db: AsyncSession,
    shift_id: UUID,
    payload: ShiftUpdate,
    request: Request | None = None,
    actor_user=None,
) -> Shift:
    shift = await _get_shift_by_id(db, shift_id)

    if shift.status not in (
        ShiftStatus.PROGRAMADO,
        ShiftStatus.CONFIRMADO,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se pueden editar turnos programados o confirmados",
        )

    changes = {}

    new_start = payload.scheduled_start or shift.scheduled_start
    new_end = payload.scheduled_end or shift.scheduled_end

    if payload.scheduled_start or payload.scheduled_end:
        if new_end <= new_start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La hora fin del turno debe ser mayor que la hora inicio",
            )

        if await _exists_shift_overlap(
            db=db,
            employee_id=shift.employee_id,
            start=new_start,
            end=new_end,
            exclude_shift_id=shift.id,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El empleado ya tiene un turno que se cruza con este horario",
            )

        shift.scheduled_start = new_start
        shift.scheduled_end = new_end

        changes["scheduled_start"] = str(new_start)
        changes["scheduled_end"] = str(new_end)

    if payload.notes is not None:
        shift.notes = payload.notes
        changes["notes"] = payload.notes

    await db.commit()

    await audit(
        db,
        action="shift.updated",
        resource="shift",
        resource_id=shift.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail=changes,
    )

    return await _get_shift_by_id(db, shift.id)


async def _change_shift_status(
    db: AsyncSession,
    shift_id: UUID,
    target_status: ShiftStatus,
    request: Request | None = None,
    actor_user=None,
) -> Shift:
    shift = await _get_shift_by_id(db, shift_id)

    if not can_transition_shift(shift.status, target_status):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se puede cambiar el turno de {shift.status.value} a {target_status.value}",
        )

    old_status = shift.status
    shift.status = target_status

    if target_status == ShiftStatus.AUSENTE and not shift.actual_start:
        shift.actual_start = None

    await db.flush()

    shift.clock_events.append(
        ClockEvent(
            shift_id=shift.id,
            employee_id=shift.employee_id,
            event_type=ShiftEventType.STATUS_CHANGED,
            ip_address=request.client.host if request and request.client else None,
            device=request.headers.get("user-agent") if request else None,
        )
    )

    await db.commit()

    await audit(
        db,
        action="shift.status_changed",
        resource="shift",
        resource_id=shift.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "old_status": old_status.value,
            "new_status": target_status.value,
        },
    )

    return await _get_shift_by_id(db, shift.id)


async def confirm_shift(
    db: AsyncSession,
    shift_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> Shift:
    return await _change_shift_status(
        db=db,
        shift_id=shift_id,
        target_status=ShiftStatus.CONFIRMADO,
        request=request,
        actor_user=actor_user,
    )


async def mark_shift_absent(
    db: AsyncSession,
    shift_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> Shift:
    return await _change_shift_status(
        db=db,
        shift_id=shift_id,
        target_status=ShiftStatus.AUSENTE,
        request=request,
        actor_user=actor_user,
    )


async def cancel_shift(
    db: AsyncSession,
    shift_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> Shift:
    return await _change_shift_status(
        db=db,
        shift_id=shift_id,
        target_status=ShiftStatus.CANCELADO,
        request=request,
        actor_user=actor_user,
    )


async def assign_tables_to_shift(
    db: AsyncSession,
    shift_id: UUID,
    payload: ShiftAssignmentUpdate,
    request: Request | None = None,
    actor_user=None,
) -> Shift:
    shift = await _get_shift_by_id(db, shift_id)

    unique_table_ids = list(dict.fromkeys(payload.table_ids))

    if unique_table_ids:
        tables = await db.scalars(
            select(Table).where(Table.id.in_(unique_table_ids))
        )

        tables_list = tables.all()

        if len(tables_list) != len(unique_table_ids):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Existen mesas inválidas en la asignación",
            )

        for table in tables_list:
            if shift.branch_id and table.branch_id != shift.branch_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Hay mesas que no pertenecen a la sucursal del turno",
                )

    shift.assignments.clear()

    for table_id in unique_table_ids:
        shift.assignments.append(
            ShiftAssignment(table_id=table_id)
        )

    await db.commit()

    await audit(
        db,
        action="shift.tables_assigned",
        resource="shift",
        resource_id=shift.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={"table_ids": [str(table_id) for table_id in unique_table_ids]},
    )

    return await _get_shift_by_id(db, shift.id)


async def generate_shifts_from_template(
    db: AsyncSession,
    payload: GenerateShiftsRequest,
    request: Request | None = None,
    actor_user=None,
) -> dict:
    template = await db.get(ShiftTemplate, payload.template_id)

    if not template or not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La plantilla de turno no es válida",
        )

    employee = await _get_employee_by_id(db, payload.employee_id)

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El empleado está inactivo",
        )

    branch_id = template.branch_id or employee.branch_id

    created = 0
    skipped = 0

    current_date = payload.date_from

    while current_date <= payload.date_to:
        if current_date.weekday() in template.weekdays:
            start_dt = datetime.combine(
                current_date,
                template.start_time,
                tzinfo=timezone.utc,
            )

            end_dt = datetime.combine(
                current_date,
                template.end_time,
                tzinfo=timezone.utc,
            )

            if template.end_time <= template.start_time:
                end_dt += timedelta(days=1)

            existing_shift = await db.scalar(
                select(Shift).where(
                    Shift.employee_id == employee.id,
                    Shift.scheduled_start == start_dt,
                )
            )

            if existing_shift:
                skipped += 1
            else:
                overlaps = await _exists_shift_overlap(
                    db=db,
                    employee_id=employee.id,
                    start=start_dt,
                    end=end_dt,
                )

                if overlaps:
                    skipped += 1
                else:
                    shift = Shift(
                        employee_id=employee.id,
                        branch_id=branch_id,
                        status=ShiftStatus.PROGRAMADO,
                        scheduled_start=start_dt,
                        scheduled_end=end_dt,
                        notes=template.notes,
                    )

                    db.add(shift)
                    created += 1

        current_date += timedelta(days=1)

    await db.commit()

    await audit(
        db,
        action="shifts.generated_from_template",
        resource="shift_template",
        resource_id=template.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "employee_id": str(employee.id),
            "date_from": str(payload.date_from),
            "date_to": str(payload.date_to),
            "created": created,
            "skipped": skipped,
        },
    )

    return {
        "created": created,
        "skipped": skipped,
    }


async def list_my_shifts(
    db: AsyncSession,
    current_user: User,
    shift_status: Optional[ShiftStatus] = None,
    date_from=None,
    date_to=None,
) -> List[Shift]:
    employee = await _get_employee_by_user_id(db, current_user.id)

    query = select(Shift).options(*shift_options()).where(
        Shift.employee_id == employee.id
    )

    if shift_status:
        query = query.where(Shift.status == shift_status)

    if date_from:
        start = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
        query = query.where(Shift.scheduled_start >= start)

    if date_to:
        end = datetime.combine(date_to, datetime.max.time(), tzinfo=timezone.utc)
        query = query.where(Shift.scheduled_start <= end)

    query = query.order_by(Shift.scheduled_start.asc())

    return (await db.scalars(query)).all()


async def _get_shift_for_clock_action(
    db: AsyncSession,
    shift_id: UUID,
    current_user: User,
) -> Shift:
    shift = await _get_shift_by_id(db, shift_id)

    if not shift.employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El empleado está inactivo",
        )

    if current_user.role not in ADMIN_SHIFT_ROLES:
        employee = await _get_employee_by_user_id(db, current_user.id)

        if shift.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para operar este turno",
            )

    return shift


def _record_clock_event(
    shift: Shift,
    event_type: ShiftEventType,
    request: Request | None = None,
) -> None:
    shift.clock_events.append(
        ClockEvent(
            shift_id=shift.id,
            employee_id=shift.employee_id,
            event_type=event_type,
            ip_address=request.client.host if request and request.client else None,
            device=request.headers.get("user-agent") if request else None,
        )
    )


async def clock_in(
    db: AsyncSession,
    shift_id: UUID,
    request: Request | None = None,
    current_user=None,
) -> Shift:
    shift = await _get_shift_for_clock_action(db, shift_id, current_user)

    if shift.status != ShiftStatus.CONFIRMADO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El turno debe estar confirmado para marcar entrada",
        )

    now = datetime.now(timezone.utc)

    scheduled_start = _ensure_utc(shift.scheduled_start)
    scheduled_end = _ensure_utc(shift.scheduled_end)

    early_limit = scheduled_start - timedelta(minutes=SHIFT_EARLY_MINUTES)
    late_limit = scheduled_end + timedelta(minutes=SHIFT_LATE_MINUTES)

    if now < early_limit:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Es demasiado temprano para marcar entrada",
        )

    if now > late_limit:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El turno está fuera de la ventana permitida para entrada",
        )

    shift.status = ShiftStatus.EN_TURNO
    shift.actual_start = now

    _record_clock_event(shift, ShiftEventType.CLOCK_IN, request)

    await db.commit()

    await audit(
        db,
        action="shift.clock_in",
        resource="shift",
        resource_id=shift.id,
        user_id=current_user.id if current_user else None,
        request=request,
        detail={
            "employee_id": str(shift.employee_id),
            "actual_start": str(shift.actual_start),
        },
    )

    return await _get_shift_by_id(db, shift.id)


async def clock_out(
    db: AsyncSession,
    shift_id: UUID,
    request: Request | None = None,
    current_user=None,
) -> Shift:
    shift = await _get_shift_for_clock_action(db, shift_id, current_user)

    if shift.status != ShiftStatus.EN_TURNO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El turno debe estar EN_TURNO para marcar salida",
        )

    if shift.active_break:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe finalizar el descanso activo antes de marcar salida",
        )

    now = datetime.now(timezone.utc)

    shift.status = ShiftStatus.FINALIZADO
    shift.actual_end = now

    _record_clock_event(shift, ShiftEventType.CLOCK_OUT, request)

    await db.commit()

    await audit(
        db,
        action="shift.clock_out",
        resource="shift",
        resource_id=shift.id,
        user_id=current_user.id if current_user else None,
        request=request,
        detail={
            "employee_id": str(shift.employee_id),
            "actual_end": str(shift.actual_end),
        },
    )

    return await _get_shift_by_id(db, shift.id)


async def start_break(
    db: AsyncSession,
    shift_id: UUID,
    request: Request | None = None,
    current_user=None,
) -> Shift:
    shift = await _get_shift_for_clock_action(db, shift_id, current_user)

    if shift.status != ShiftStatus.EN_TURNO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se puede iniciar descanso cuando el turno está EN_TURNO",
        )

    if shift.active_break:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ya existe un descanso activo",
        )

    now = datetime.now(timezone.utc)

    shift.breaks.append(
        ShiftBreak(
            shift_id=shift.id,
            started_at=now,
        )
    )

    shift.status = ShiftStatus.EN_DESCANSO

    _record_clock_event(shift, ShiftEventType.BREAK_START, request)

    await db.commit()

    await audit(
        db,
        action="shift.break_started",
        resource="shift",
        resource_id=shift.id,
        user_id=current_user.id if current_user else None,
        request=request,
        detail={"employee_id": str(shift.employee_id)},
    )

    return await _get_shift_by_id(db, shift.id)


async def end_break(
    db: AsyncSession,
    shift_id: UUID,
    request: Request | None = None,
    current_user=None,
) -> Shift:
    shift = await _get_shift_for_clock_action(db, shift_id, current_user)

    if shift.status != ShiftStatus.EN_DESCANSO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El turno no está en descanso",
        )

    active_break = shift.active_break

    if not active_break:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No existe un descanso activo",
        )

    now = datetime.now(timezone.utc)

    active_break.ended_at = now
    shift.status = ShiftStatus.EN_TURNO

    _record_clock_event(shift, ShiftEventType.BREAK_END, request)

    await db.commit()

    await audit(
        db,
        action="shift.break_ended",
        resource="shift",
        resource_id=shift.id,
        user_id=current_user.id if current_user else None,
        request=request,
        detail={"employee_id": str(shift.employee_id)},
    )

    return await _get_shift_by_id(db, shift.id)
