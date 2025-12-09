from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.config.auth import security
from app.database import get_db
from app.schemas.jwt_token_schema import LogoutRequest
from app.schemas.user_schema import UserLoginScheme, UserRegisterScheme, ForgotPasswordScheme, ResetPasswordScheme
from app.services.auth_service import register_user, login_user, activate_user, forgot_password_service, \
    reset_password_service, logout_service, refresh_token_service

router = APIRouter(prefix="/user", tags=["user"])
securityCred = HTTPBearer()

@router.post("/register")
async def register(user_data: UserRegisterScheme, db: AsyncSession = Depends(get_db)):
    await register_user(db, user_data)

    return {"message": "User registered. Please check your email to activate your account."}

@router.post("/login")
async def login(user_data: UserLoginScheme, db: AsyncSession = Depends(get_db)):
    return await login_user(db, user_data)

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

@router.post("/reset-password")
async def reset_password(user_data: ResetPasswordScheme, token_str: str = Query(...), db: AsyncSession = Depends(get_db)):
    return await reset_password_service(db, token_str, user_data.password)

@router.post("/refresh-token")
async def refresh_token_route(
    credentials: HTTPAuthorizationCredentials = Depends(securityCred),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials
    return await refresh_token_service(db, token)