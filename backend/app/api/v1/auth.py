from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import bearer_scheme, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse
from app.services import auth_service


router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login de personal",
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.login(
        db=db,
        request=request,
        email=payload.email,
        password=payload.password,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token",
)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.refresh_tokens(
        db=db,
        request=request,
        refresh_token=payload.refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión y revocar token",
)
async def logout(
    payload: LogoutRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )

    await auth_service.logout(
        db=db,
        request=request,
        access_token=credentials.credentials,
        refresh_token=payload.refresh_token,
        current_user=current_user,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
