from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.schemas.user_schema import UserRead

class CreateProject(BaseModel):
    name: str
    purpose_id: int
    description: str
    users: list[EmailStr]

class ProjectRead(BaseModel):
    name: str
    description: str
    created_at: datetime

    creator: UserRead

    class Config:
        from_attributes = True

class PurposesRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class AddProjectMember(BaseModel):
    project_id: int
    user_id: int
    role_id: int

class JoinProjectRequest(BaseModel):
    token: str