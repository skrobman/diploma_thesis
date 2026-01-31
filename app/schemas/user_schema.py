from pydantic import BaseModel, EmailStr

class UserRegisterScheme(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    name: str
    surname: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }

class ProfileRead(BaseModel):
    name: str
    surname: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }

class ChangeUsername(BaseModel):
    name: str | None = None
    surname: str | None = None
class ChangePasswordScheme(BaseModel):
    old_password: str
    new_password: str

class UserLoginScheme(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordScheme(BaseModel):
    email: EmailStr

class ResetPasswordByTokenScheme(BaseModel):
    token: str
    password: str

class ResetPasswordScheme(BaseModel):
    password: str