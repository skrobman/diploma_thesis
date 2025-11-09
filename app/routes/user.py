import traceback

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.config.auth import security
from app.database import get_db
from app.schemas.user_schema import UserLoginScheme, UserRegisterScheme, ForgotPasswordScheme, ResetPasswordScheme
from app.services.auth_service import register_user, login_user, activate_user, forgot_password_service, \
    reset_password_service

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/register")
def register(user_data: UserRegisterScheme, db: Session = Depends(get_db)):
    try:
        register_user(db, user_data)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "User registered. Please check your email to activate your account."}

@router.post("/login")
def login(user_data: UserLoginScheme, db: Session = Depends(get_db)):
    return login_user(db, user_data)

@router.get("/activate")
def activate_account(token: str = Query(...), db: Session = Depends(get_db)):
    return activate_user(db, token)

@router.post("/logout", dependencies=[Depends(security.access_token_required)])
def logout():
    return {"message": "Successfully logged out"}

@router.post("/forgot_password")
def forgot_password(user_data: ForgotPasswordScheme, db: Session = Depends(get_db)):
    return forgot_password_service(db, user_data.email)

@router.post("/reset-password")
def reset_password(user_data: ResetPasswordScheme, token_str: str = Query(...), db: Session = Depends(get_db)):
    return reset_password_service(db, token_str, user_data.password)