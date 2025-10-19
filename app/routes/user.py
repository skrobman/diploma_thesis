from fastapi import APIRouter, Response,Depends
from app.config.auth import security, config
from app.database import session
from app.schemas.user_schema import UserLoginScheme, UserRegisterScheme
from app.services.auth_service import register_user, login_user, activate_user

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/register")
async def register(user_data: UserRegisterScheme):
    user = register_user(session, user_data.full_name, user_data.email, user_data.password)
    return {"message": "User registered. Please check your email to activate your account."}

@router.post("/login")
async def login(user_data: UserLoginScheme, response: Response):
    token = login_user(session, user_data.email, user_data.password)
    response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
    return {"access_token": token}

@router.get("/activate/{token_str}")
def activate_account(token_str: str):
    activate_user(session, token_str)
    return {"message": "Account successfully activated!"}

@router.post("/logout", dependencies=[Depends(security.access_token_required)])
async def logout(response: Response):
    response.delete_cookie(config.JWT_ACCESS_COOKIE_NAME)
    return {"message": "Successfully logged out"}