import uuid
from datetime import datetime, timedelta

import bcrypt
from fastapi import HTTPException
from jose import JWTError, jwt
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.config.auth import security
from app.models.models import User, ActivationToken
from app.repositories.activation_token_repository import save_activation_token, get_activation_token, \
    delete_activation_token
from app.repositories.jwt_token_repository import save_jwt_token, verify_jwt_token, revoke_refresh_token
from app.repositories.user_repository import get_user_by_email, create_user
from app.schemas.user_schema import UserRegisterScheme, UserLoginScheme
from app.services.mail_service import send_email
from app.utils.rateLimiters.rate_limiters import FORGOT_PASSWORD_LIMITER, LOGIN_LIMITER


def _create_user_tokens(db: Session, user: User) -> dict:
    access_token = security.create_access_token(
        uid=str(user.id),
        data={"email": user.email}
    )

    # Refresh Token
    refresh_token = security.create_refresh_token(
        uid=str(user.id),
        data={"email": user.email}
    )

    save_jwt_token(db, user, refresh_token)

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


def refresh_token_service(db: Session, token: str):
    verify_jwt_token(db, token)

    try:
        SECRET_KEY = security.config.JWT_SECRET_KEY
        ALGORITHM = "HS256"

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

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tokens = _create_user_tokens(db, user)

    revoke_refresh_token(db, token)

    return tokens

def register_user(db: Session, data: UserRegisterScheme):
    if get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Account already exists")

    password_hash = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    new_user = create_user(db, data.full_name, data.email, password_hash)

    token = create_activation_token(new_user, "activation_token")
    save_activation_token(db, token)

    activation_link = f"https://diploma-thesis.onrender.com/user/activate?token={token.token}"
    activation_link2 = f"http://localhost:8000/user/activate?token={token.token}"
    send_email(
        to_email=new_user.email,
        subject="Activate your account",
        text=f"Hello! Activate your account using: {activation_link}",
        html=f"<p>Hello! Activate your account using: <a href='{activation_link}'>link</a></p>"
    )

    return new_user

def login_user(db: Session, data: UserLoginScheme):
    user = get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Account not activated")

    if not bcrypt.checkpw(data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        # проверяем, достигнут ли лимит после увеличения
        if not LOGIN_LIMITER.is_allowed(data.email):
            raise HTTPException(
                status_code=429,
                detail="Too many failed login attempts. Try again later."
            )

        raise HTTPException(status_code=401, detail="Incorrect password")

    LOGIN_LIMITER.delete(data.email)

    return _create_user_tokens(db, user)

def activate_user(db: Session, token_str: str):
    token = get_activation_token(db, token_str, 'activation_token')
    if not token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if token.expiry_date < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    user = token.user
    user.status = 'active'
    delete_activation_token(db, token)

    return _create_user_tokens(db,user)

def forgot_password_service(db: Session, email: EmailStr):
    if not FORGOT_PASSWORD_LIMITER.is_allowed(str(email)):
        remaining = FORGOT_PASSWORD_LIMITER.get_remaining(str(email))
        raise HTTPException(
            status_code=429,
            detail=f"Too many password reset requests. Try again later. Remaining attempts: {remaining}"
        )

    user = get_user_by_email(db, email)

    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")

    token = create_activation_token(user, "forgot_password")
    save_activation_token(db, token)

    activation_link = f"https://diploma-thesis.onrender.com/user/reset-password?token={token.token}"
    activation_link2 = f"http://localhost:8000/user/reset-password?token={token.token}"
    send_email(
        to_email=user.email,
        subject="Reset your password",
        text=f"Hello! Reset your password using: {activation_link}",
        html=f"<p>Hello! Reset your password using: <a href='{activation_link}'>link</a></p>"
             f"<p>If you didn't click, just ignore the message</p>"
    )

    return {"message": "Reset link sent to your email"}

def reset_password_service(db: Session, token_str: str, new_password: str):
    token = get_activation_token(db, token_str, 'forgot_password')
    if not token:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = token.user
    if bcrypt.checkpw(new_password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the old one")

    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    delete_activation_token(db, token)

    return {"message": "Password reset successfully"}

def logout_service(db: Session, token_str: str):
    verify_jwt_token(db, token_str)

    revoke_refresh_token(db, token_str)

    return {"message": "Successfully logged out"}