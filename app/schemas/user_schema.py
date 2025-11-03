from pydantic import BaseModel, EmailStr

class UserRegisterScheme(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True

class UserLoginScheme(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordScheme(BaseModel):
    email: EmailStr

class ResetPasswordScheme(BaseModel):
    password: str