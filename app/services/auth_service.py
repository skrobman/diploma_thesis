import uuid
from datetime import datetime, timedelta

import bcrypt
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.config.auth import security
from app.models.models import User, ActivationToken
from app.services.mail_service import send_email

def _create_user_tokens(user: User) -> dict:
    access_token = security.create_access_token(
        uid=str(user.id),
        data={"email": user.email}
    )

    # Refresh Token
    refresh_token = security.create_refresh_token(
        uid=str(user.id),
        data={"email": user.email}
    )

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

def register_user(db: Session, full_name: str, email: EmailStr, password: str):
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(status_code=400, detail="Account already exists")

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = User(full_name=full_name, email=email, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_activation_token(new_user, "activation_token")
    db.add(token)
    db.commit()

    activation_link = f"https://diploma-thesis.onrender.com/user/activate?token={token.token}"
    # activation_link2 = f"http://localhost:8000/user/activate?token={token.token}"
    send_email(
        to_email=new_user.email,
        subject="Activate your account",
        text=f"Hello! Activate your account using: {activation_link}",
        html=f"<p>Hello! Activate your account using: <a href='{activation_link}'>link</a></p>"
    )

    return new_user

def login_user(db: Session, email: EmailStr, password: str):
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Account not activated")

    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return _create_user_tokens(user)

def activate_user(db: Session, token_str: str):
    token = db.query(ActivationToken).filter_by(token=token_str).first()
    if not token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if token.expiry_date < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    user = token.user
    user.status = 'active'
    db.delete(token)
    db.commit()

    return _create_user_tokens(user)

def forgot_password_service(db: Session, email: EmailStr):
    user = db.query(User).filter_by(email = email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")

    token = create_activation_token(user, "forgot_password")
    db.add(token)
    db.commit()

    activation_link = f"https://diploma-thesis.onrender.com/user/reset-password?token={token.token}"
    send_email(
        to_email=user.email,
        subject="Reset your password",
        text=f"Hello! Reset your password using: {activation_link}",
        html=f"<p>Hello! Reset your password using: <a href='{activation_link}'>link</a></p>"
             f"<p>If you didn't click, just ignore the message</p>"
    )

    return {"message": "Reset link sent to your email"}

def reset_password_service(db: Session, token_str: str, new_password: str):
    token = db.query(ActivationToken).filter_by(token=token_str, token_purpose="forgot_password").first()
    if not token:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = token.user
    if bcrypt.checkpw(new_password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the old one")

    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.delete(token)
    db.commit()

    return {"message": "Password reset successfully"}