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

    model_config = {
        "from_attributes": True
    }

class ProjectRead(BaseModel):
    id: int
    name: str
    description: str
    is_archived: bool
    creator: UserRead
    created_at: datetime

    members: list[ProjectMemberRead] = []

    model_config = {"from_attributes": True}

class AllProjectsResponse(BaseModel):
    items: List[ProjectRead]
    total: int
    next_cursor: Optional[int] = None

    model_config = {"from_attributes": True}

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

class UpdateProjectMemberRole(BaseModel):
    user_email: EmailStr
    role_id: int

class UpdateProjectArchiveStatus(BaseModel):
    is_archived: bool