from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.user_schema import UserRead


class CreateTask(BaseModel):
    project_name: str
    name: str
    priority_id: int
    description: str = None
    start_at: datetime
    deadline_at: datetime
    users: list[int]

class TaskMemberRead(BaseModel):
    role: str
    users: UserRead

    model_config = {"from_attributes": True}

class ReadTask(BaseModel):
    id: int
    name: str
    priority_id: int
    priority_name: str
    created_by: UserRead
    weight: int
    description: str
    start_at: datetime
    deadline_at: datetime
    members: list[TaskMemberRead]

    model_config = {"from_attributes": True}

class AllTasksResponse(BaseModel):
    items: List[ReadTask]
    next_cursor: Optional[int] = None

    model_config = {"from_attributes": True}
