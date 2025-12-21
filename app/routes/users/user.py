from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from app.config.auth import security
from app.config.dependencies import get_current_user
from app.database import get_db
from app.models.models import User
from app.schemas.jwt_token_schema import LogoutRequest
from app.schemas.user_schema import UserLoginScheme, UserRegisterScheme, ForgotPasswordScheme, ResetPasswordScheme, \
    ResetPasswordByTokenScheme
from app.services.auth_service import register_user, login_user, activate_user, forgot_password_service, \
    reset_password_service, logout_service, refresh_token_service, reset_password_by_token_service, \
    check_reset_password_token_service, get_user_profile_service

router = APIRouter(prefix="/user", tags=["user"])
securityCred = HTTPBearer()

@router.post("/register")
async def register(user_data: UserRegisterScheme, db: AsyncSession = Depends(get_db)):
    await register_user(db, user_data)

    return {"message": "User registered. Please check your email to activate your account."}

@router.post("/login")
async def login(user_data: UserLoginScheme, db: AsyncSession = Depends(get_db)):
    tokens = await login_user(db, user_data)

    response = JSONResponse(
        content={
            "access_token": tokens["access_token"],
            "token_type": "bearer",
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    return response

@router.get(
    "/activate",
    status_code=status.HTTP_200_OK
)
async def activate_account(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    await activate_user(db, token)

    return {"message": "Account successfully activated!"}

@router.post("/logout", dependencies=[Depends(security.access_token_required)])
async def logout(data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    return await logout_service(db, data.refresh_token)

@router.post("/forgot_password")
async def forgot_password(user_data: ForgotPasswordScheme, db: AsyncSession = Depends(get_db)):
    return await forgot_password_service(db, user_data.email)

@router.get("/reset_password")
async def check_reset_password_token(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    return await check_reset_password_token_service(db, token)

@router.post("/reset-password-by-token")
async def reset_password_by_token(
        user_data: ResetPasswordByTokenScheme,
        db: AsyncSession = Depends(get_db)
):
    return await reset_password_by_token_service(db, user_data.token, user_data.password)

@router.post("/reset-password")
async def reset_password(
        user_data: ResetPasswordScheme,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await reset_password_service(db, current_user.id, user_data.password)

@router.post("/refresh-token")
async def refresh_token_route(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    tokens = await refresh_token_service(db, refresh_token)

    response = JSONResponse(
        content={
            "access_token": tokens["access_token"],
            "token_type": "bearer",
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    return response