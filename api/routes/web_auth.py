from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.web_auth_service import WebAuthService
from api.models.requests import WebUserLogin, TokenRefresh
from api.models.responses import WebUserResponse, WebTokenResponse, WebTokenRefreshResponse
from api.models.entities import WebUser
from api.dependencies.auth_dependencies import get_current_web_user
from api.dependencies.rate_limiter import check_login_rate_limit, record_failed_login, clear_failed_login

router = APIRouter(prefix="/web/auth", tags=["web-auth"])


@router.post("/login", response_model=WebTokenResponse)
async def web_login(
    data: WebUserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await check_login_rate_limit(request, data.email)

    service = WebAuthService(db)
    try:
        result = await service.login(data.email, data.password)
    except Exception:
        await record_failed_login(data.email)
        raise

    await clear_failed_login(data.email)
    return WebTokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
        user=WebUserResponse.model_validate(result["user"]),
    )


@router.get("/me", response_model=WebUserResponse)
async def web_me(
    web_user: WebUser = Depends(get_current_web_user),
):
    return WebUserResponse.model_validate(web_user)


@router.post("/refresh", response_model=WebTokenRefreshResponse)
async def web_refresh(
    data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    result = await service.refresh_token(data.refresh_token)
    return WebTokenRefreshResponse(**result)


@router.post("/logout")
async def web_logout(
    web_user: WebUser = Depends(get_current_web_user),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    await service.revoke_token(web_user)
    return {"message": "Успешный выход из системы"}
