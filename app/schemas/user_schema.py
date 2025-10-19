from pydantic import BaseModel, EmailStr

class UserRegisterScheme(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLoginScheme(BaseModel):
    email: EmailStr
    password: str