from fastapi import APIRouter, Response, Depends, Query
from sqlalchemy.orm import Session

from app.config.auth import security, config
from app.database import get_db
from app.schemas.user_schema import UserLoginScheme, UserRegisterScheme, ForgotPasswordScheme, ResetPasswordScheme
from app.services.auth_service import register_user, login_user, activate_user, forgot_password_service, \
    reset_password_service

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/register")
async def register(user_data: UserRegisterScheme, db: Session = Depends(get_db)):
    user = register_user(db, user_data.full_name, user_data.email, user_data.password)
    return {"message": "User registered. Please check your email to activate your account."}

@router.post("/login")
async def login(user_data: UserLoginScheme, response: Response, db: Session = Depends(get_db)):
    token = login_user(db, user_data.email, user_data.password)
    response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
    return {"access_token": token}

@router.get("/activate")
def activate_account(token: str = Query(...), db: Session = Depends(get_db)):
    activate_user(db, token)
    return {"message": "Account successfully activated!"}

@router.post("/logout", dependencies=[Depends(security.access_token_required)])
async def logout(response: Response):
    response.delete_cookie(config.JWT_ACCESS_COOKIE_NAME)
    return {"message": "Successfully logged out"}

@router.post("/forgot_password")
async def forgot_password(user_data: ForgotPasswordScheme, db: Session = Depends(get_db)):
    return forgot_password_service(db, user_data.email)

@router.post("/reset-password")
async def reset_password(user_data: ResetPasswordScheme, token_str: str = Query(...), db: Session = Depends(get_db)):
    return reset_password_service(db, token_str, user_data.password)