import uuid
from datetime import datetime, timedelta
import bcrypt
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session


from app.config.auth import security
from app.models.models import User, ActivationToken
from app.services.mail_service import send_email

def create_activation_token(user: User):
    token_str = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(minutes=15)
    token = ActivationToken(token=token_str, user=user, expiry_date=expiry)
    return token

def register_user(db: Session, full_name: str, email: EmailStr, password: str):
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(status_code=400, detail="Account already exists")

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = User(full_name=full_name, email=email, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_activation_token(new_user)
    db.add(token)
    db.commit()

    activation_link = f"http://localhost:8000/user/activate/{token.token}"
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

    token = security.create_access_token(uid=str(user.id), data={"email": user.email})
    return token

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
    return user
