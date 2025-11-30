from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, computed_field

from app.schemas.user_schema import UserRead
from app.utils.date_utils import time_ago


class CreateProject(BaseModel):
    name: str
    purpose_id: int
    description: str
    users: list[EmailStr] = []

class ProjectMemberRead(BaseModel):
    role_id: int
    user: UserRead

    class Config:
        from_attributes = True

class ProjectRead(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    members: list[ProjectMemberRead] = []

    @computed_field
    def last_activity(self) -> str:
        return time_ago(self.updated_at)


    class Config:
        from_attributes = True

class AllProjectsResponse(BaseModel):
    items: List[ProjectRead]
    total: int
    next_cursor: Optional[int] = None

class PurposesRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class RolesRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class AddProjectMember(BaseModel):
    project_id: int
    user_id: int
    role_id: int

class InviteUserRequest(BaseModel):
    emails: List[EmailStr]

class JoinProjectRequest(BaseModel):
    token: str

class UpdateProject(BaseModel):
    name: str | None = None
    description: str | None = None
