from datetime import datetime, timezone, time
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr

from app.schemas.user_schema import UserRead

def today_start():
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

def today_end():
    return datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=0)

class PrioritiesRead(BaseModel):
    id: int
    name: str
    weight: int

class CreateTask(BaseModel):
    project_id: int
    name: str
    priority_id: int
    description: str = None
    start_at: datetime = Field(default_factory=today_start)
    deadline_at: datetime = Field(default_factory=today_end)
    deadline_time: time | None = None
    users: list[EmailStr] = []

    @field_validator('start_at', 'deadline_at')
    def force_utc(cls, v: datetime):
        #Если фронт прислал время без зоны, считаем, что это UTC
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)

        # Если фронт прислал время с зоной - переводим в UTC,
        # переводим его в UTC
        return v.astimezone(timezone.utc)

    @model_validator(mode='after')
    def check_dates_order(self):
        if self.start_at > self.deadline_at:
            raise ValueError('Deadline must be after start')
        return self

class TaskMemberRead(BaseModel):
    role: str
    users: UserRead

    model_config = {"from_attributes": True}

class CalendarTasksRead(BaseModel):
    project_id: int
    task_id: int
    name: str
    description: str
    priority_id: int
    start_at: datetime
    deadline_at: datetime
    is_overdue: bool = False
    is_completed: bool

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_is_overdue(cls, values):
        # values — это объект модели
        values.is_overdue = values.deadline_at < datetime.now(timezone.utc)
        return values

class ReadCreatedTask(BaseModel):
    project_id: int
    name: str
    description: str = None
    priority_name: str
    is_completed: bool
    start_at: datetime
    deadline_at: datetime
    created_by: UserRead
    members: list[TaskMemberRead]

    model_config = {"from_attributes": True}

class ReadTask(BaseModel):
    id: int
    name: str
    priority_id: int
    priority_name: str | None = None
    created_by: UserRead
    weight: int | None
    description: str
    is_completed: bool
    start_at: datetime
    deadline_at: datetime
    members: list[TaskMemberRead]

    model_config = {"from_attributes": True}

class AllTasksResponse(BaseModel):
    items: List[ReadTask]
    next_cursor: Optional[int] = None

    model_config = {"from_attributes": True}
