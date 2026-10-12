from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.enums import ShiftStatus, UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.turnos import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
    GenerateShiftsRequest,
    GenerateShiftsResult,
    ShiftAssignmentUpdate,
    ShiftCreate,
    ShiftRead,
    ShiftTemplateCreate,
    ShiftTemplateRead,
    ShiftTemplateUpdate,
    ShiftUpdate,
)
from app.services import turnos_service


router = APIRouter()
admin_router = APIRouter()


@router.get(
    "/turnos/mis-turnos",
    response_model=List[ShiftRead],
    summary="Consultar mis turnos",
)
async def my_shifts(
    shift_status: ShiftStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.list_my_shifts(
        db=db,
        current_user=current_user,
        shift_status=shift_status,
        date_from=date_from,
        date_to=date_to,
    )


@router.post(
    "/turnos/{shift_id}/entrada",
    response_model=ShiftRead,
    summary="Marcar entrada",
)
async def clock_in(
    shift_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.clock_in(
        db=db,
        shift_id=shift_id,
        request=request,
        current_user=current_user,
    )


@router.post(
    "/turnos/{shift_id}/salida",
    response_model=ShiftRead,
    summary="Marcar salida",
)
async def clock_out(
    shift_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.clock_out(
        db=db,
        shift_id=shift_id,
        request=request,
        current_user=current_user,
    )


@router.post(
    "/turnos/{shift_id}/descanso/iniciar",
    response_model=ShiftRead,
    summary="Iniciar descanso",
)
async def start_break(
    shift_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.start_break(
        db=db,
        shift_id=shift_id,
        request=request,
        current_user=current_user,
    )


@router.post(
    "/turnos/{shift_id}/descanso/finalizar",
    response_model=ShiftRead,
    summary="Finalizar descanso",
)
async def end_break(
    shift_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.end_break(
        db=db,
        shift_id=shift_id,
        request=request,
        current_user=current_user,
    )


@admin_router.get(
    "/empleados",
    response_model=List[EmployeeRead],
    summary="Listar empleados",
)
async def list_employees(
    branch_id: UUID | None = None,
    include_inactive: bool = False,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.list_employees(db, branch_id, include_inactive)


@admin_router.post(
    "/empleados",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empleado",
)
async def create_employee(
    payload: EmployeeCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.create_employee(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/empleados/{employee_id}",
    response_model=EmployeeRead,
    summary="Ver empleado",
)
async def get_employee(
    employee_id: UUID,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.get_employee(db, employee_id)


@admin_router.patch(
    "/empleados/{employee_id}",
    response_model=EmployeeRead,
    summary="Actualizar empleado",
)
async def update_employee(
    employee_id: UUID,
    payload: EmployeeUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.update_employee(
        db=db,
        employee_id=employee_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/turnos/plantillas",
    response_model=List[ShiftTemplateRead],
    summary="Listar plantillas de turno",
)
async def list_shift_templates(
    include_inactive: bool = False,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.list_shift_templates(db, include_inactive)


@admin_router.post(
    "/turnos/plantillas",
    response_model=ShiftTemplateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear plantilla de turno",
)
async def create_shift_template(
    payload: ShiftTemplateCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.create_shift_template(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.patch(
    "/turnos/plantillas/{template_id}",
    response_model=ShiftTemplateRead,
    summary="Actualizar plantilla de turno",
)
async def update_shift_template(
    template_id: UUID,
    payload: ShiftTemplateUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.update_shift_template(
        db=db,
        template_id=template_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.post(
    "/turnos/generar",
    response_model=GenerateShiftsResult,
    summary="Generar turnos desde plantilla",
)
async def generate_shifts(
    payload: GenerateShiftsRequest,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.generate_shifts_from_template(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/turnos",
    response_model=List[ShiftRead],
    summary="Listar turnos",
)
async def list_shifts(
    employee_id: UUID | None = None,
    branch_id: UUID | None = None,
    shift_status: ShiftStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.list_shifts_admin(
        db=db,
        employee_id=employee_id,
        branch_id=branch_id,
        shift_status=shift_status,
        date_from=date_from,
        date_to=date_to,
    )


@admin_router.post(
    "/turnos",
    response_model=ShiftRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear turno manual",
)
async def create_shift(
    payload: ShiftCreate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.create_shift(
        db=db,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.get(
    "/turnos/{shift_id}",
    response_model=ShiftRead,
    summary="Ver turno",
)
async def get_shift(
    shift_id: UUID,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.get_shift_admin(db, shift_id)


@admin_router.patch(
    "/turnos/{shift_id}",
    response_model=ShiftRead,
    summary="Actualizar turno",
)
async def update_shift(
    shift_id: UUID,
    payload: ShiftUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.update_shift(
        db=db,
        shift_id=shift_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )


@admin_router.post(
    "/turnos/{shift_id}/confirmar",
    response_model=ShiftRead,
    summary="Confirmar turno",
)
async def confirm_shift(
    shift_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.confirm_shift(
        db=db,
        shift_id=shift_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.post(
    "/turnos/{shift_id}/ausente",
    response_model=ShiftRead,
    summary="Marcar ausencia",
)
async def mark_absent(
    shift_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.mark_shift_absent(
        db=db,
        shift_id=shift_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.post(
    "/turnos/{shift_id}/cancelar",
    response_model=ShiftRead,
    summary="Cancelar turno",
)
async def cancel_shift(
    shift_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.cancel_shift(
        db=db,
        shift_id=shift_id,
        request=request,
        actor_user=current_user,
    )


@admin_router.put(
    "/turnos/{shift_id}/mesas",
    response_model=ShiftRead,
    summary="Asignar mesas al turno",
)
async def assign_tables(
    shift_id: UUID,
    payload: ShiftAssignmentUpdate,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.RRHH)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await turnos_service.assign_tables_to_shift(
        db=db,
        shift_id=shift_id,
        payload=payload,
        request=request,
        actor_user=current_user,
    )
