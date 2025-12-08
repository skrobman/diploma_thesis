import asyncio
import uuid
from datetime import datetime, timedelta
import logging

import bcrypt
from fastapi import HTTPException
from jose import JWTError, jwt
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.auth import security
from app.config.config import settings
from app.models.models import User, ActivationToken
from app.repositories.token_repositories.activation_token_repository import save_activation_token, get_activation_token, \
    delete_activation_token
from app.repositories.token_repositories.jwt_token_repository import save_jwt_token, verify_jwt_token, revoke_refresh_token
from app.repositories.user_repository import get_user_by_email, create_user, get_user_by_id
from app.schemas.user_schema import UserRegisterScheme, UserLoginScheme
from app.services.mail_service import send_email
from app.utils.rateLimiters.rate_limiters import FORGOT_PASSWORD_LIMITER, LOGIN_LIMITER

from app.utils.error_handler import handle_db_errors

logger = logging.getLogger(__name__)

async def _create_user_tokens(db: AsyncSession, user: User) -> dict:
    access_token = security.create_access_token(
        uid=str(user.id),
        data={"email": user.email}
    )

    # Refresh Token
    refresh_token = security.create_refresh_token(
        uid=str(user.id),
        data={"email": user.email}
    )

    await save_jwt_token(db, user, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

def create_activation_token(user: User, purpose: str):
    token_str = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(minutes=15)
    token = ActivationToken(token=token_str, user_id=user.id, expiry_date=expiry, token_purpose=purpose)
    return token

@handle_db_errors
async def refresh_token_service(db: AsyncSession, token: str):
    await verify_jwt_token(db, token)

    try:
        SECRET_KEY = security.config.JWT_SECRET_KEY
        ALGORITHM = security.config.JWT_ALGORITHM

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type, expected 'refresh'")

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {e}"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tokens = await _create_user_tokens(db, user)

    await revoke_refresh_token(db, token)

    return tokens

@handle_db_errors
async def register_user(db: AsyncSession, data: UserRegisterScheme):
    # if await get_user_by_email(db, data.email):
    #     raise HTTPException(status_code=400, detail="Account already exists")

    password_hash = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        new_user = await create_user(db, data.full_name, data.email, password_hash)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = create_activation_token(new_user, "activation_token")
    await save_activation_token(db, token)

    try:
        activation_link = f"{settings.FRONTEND_URL}/verified-email?token={token.token}"
        activation_link2 = f"{settings.BASE_LINK}/user/activate?token={token.token}"
        await send_email(
            to_email=new_user.email,
            subject="Activate your account",
            text=f"Hello! Activate your account using: {activation_link}",
            html=f"<p>Hello! Activate your account using: <a href='{activation_link}'>link</a></p>"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"An unexpected error occurred in sending email: {e}")

    return new_user

@handle_db_errors
async def login_user(db: AsyncSession, data: UserLoginScheme):
    user = await get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Account not activated")

    password_correct = await asyncio.to_thread(
        bcrypt.checkpw,
        data.password.encode('utf-8'),
        user.password_hash.encode('utf-8')
    )

    if not password_correct:
        if not await LOGIN_LIMITER.is_allowed(data.email):
            raise HTTPException(
                status_code=429,
                detail="Too many failed login attempts. Try again later."
            )
        raise HTTPException(status_code=401, detail="Incorrect password")

    await LOGIN_LIMITER.delete(data.email)

    return await _create_user_tokens(db, user)

@handle_db_errors
async def activate_user(db: AsyncSession, token_str: str):
    token = await get_activation_token(db, token_str, 'activation_token')
    if not token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if token.expiry_date < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    user = await get_user_by_id(db, token.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.status = 'active'
    await delete_activation_token(db, token)

@handle_db_errors
async def forgot_password_service(db: AsyncSession, email: EmailStr):
    if not await FORGOT_PASSWORD_LIMITER.is_allowed(str(email)):
        remaining = await FORGOT_PASSWORD_LIMITER.get_remaining(str(email))
        raise HTTPException(
            status_code=429,
            detail=f"Too many password reset requests. Try again later. Remaining attempts: {remaining}"
        )

    user = await get_user_by_email(db, email)

    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")

    token = create_activation_token(user, "forgot_password")
    await save_activation_token(db, token)

    try:
        activation_link = f"{settings.RENDER_LINK}/user/reset-password?token={token.token}"
        activation_link2 = f"{settings.BASE_LINK}/user/reset-password?token={token.token}"
        await send_email(
            to_email=user.email,
            subject="Reset your password",
            text=f"Hello! Reset your password using: {activation_link}",
            html=f"<p>Hello! Reset your password using: <a href='{activation_link}'>link</a></p>"
                 f"<p>If you didn't click, just ignore the message</p>"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"An unexpected error occurred in sending email: {e}")

    return {"message": "Reset link sent to your email"}

@handle_db_errors
async def reset_password_service(db: AsyncSession, token_str: str, new_password: str):
    token = await get_activation_token(db, token_str, 'forgot_password')
    if not token:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = await get_user_by_id(db, token.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if bcrypt.checkpw(new_password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the old one")

    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    await delete_activation_token(db, token)

    return {"message": "Password reset successfully"}

@handle_db_errors
async def logout_service(db: AsyncSession, token_str: str):
    await verify_jwt_token(db, token_str)

    await revoke_refresh_token(db, token_str)

    return {"message": "Successfully logged out"}