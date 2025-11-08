from fastapi import APIRouter, Response, Depends, Query
from sqlalchemy.orm import Session

from app.config.auth import security, config
from app.database import get_db
from app.schemas.user_schema import UserLoginScheme, UserRegisterScheme, ForgotPasswordScheme, ResetPasswordScheme
from app.services.auth_service import register_user, login_user, activate_user, forgot_password_service, \
    reset_password_service

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/register")
def register(user_data: UserRegisterScheme, db: Session = Depends(get_db)):
    user = register_user(db, user_data.full_name, user_data.email, user_data.password)
    return {"message": "User registered. Please check your email to activate your account."}

@router.post("/login")
def login(user_data: UserLoginScheme, db: Session = Depends(get_db)):
    return login_user(db, user_data.email, user_data.password)

@router.get("/activate")
def activate_account(token: str = Query(...), db: Session = Depends(get_db)):
    return activate_user(db, token)

@router.post("/logout", dependencies=[Depends(security.access_token_required)])
def logout(response: Response):
    return {"message": "Successfully logged out"}

@router.post("/forgot_password")
def forgot_password(user_data: ForgotPasswordScheme, db: Session = Depends(get_db)):
    return forgot_password_service(db, user_data.email)

@router.post("/reset-password")
def reset_password(user_data: ResetPasswordScheme, token_str: str = Query(...), db: Session = Depends(get_db)):
    return reset_password_service(db, token_str, user_data.password)