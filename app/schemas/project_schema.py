from datetime import datetime

from pydantic import BaseModel

from app.schemas.user_schema import UserRead


class CreateProject(BaseModel):
    name: str
    purpose_id: int
    description: str

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
