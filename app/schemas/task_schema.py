from datetime import datetime, timezone, time, date
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

    start_at: datetime | None = None
    start_date: date | None = None
    start_time: time | None = None

    deadline_at: datetime | None = None
    deadline_date: date | None = None
    deadline_time: time | None = None

    users: list[EmailStr] = []

    without_time: bool = False

    @model_validator(mode="after")
    def compute_datetimes(cls, values: "CreateTask"):
        # Если пришли datetime
        if values.start_at and values.deadline_at:
            values.without_time = False
            return values

        # Если есть только start_date
        start_date = values.start_date
        start_time = values.start_time
        deadline_date = values.deadline_date or start_date
        deadline_time = values.deadline_time

        if not start_date:
            raise ValueError("start_date must be provided if start_at not sent")

        # start_at
        start_at = datetime.combine(start_date, start_time or time.min, tzinfo=timezone.utc)
        values.start_at = start_at

        # deadline_at
        if deadline_time:
            deadline_at = datetime.combine(deadline_date, deadline_time, tzinfo=timezone.utc)
            values.without_time = False
        else:
            deadline_at = datetime.combine(deadline_date, time.max, tzinfo=timezone.utc)
            values.without_time = True

        values.deadline_at = deadline_at

        # если start_time есть → без времени нет
        if start_time:
            values.without_time = False

        return values

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
    without_time: bool
    members: list[TaskMemberRead]

    model_config = {"from_attributes": True}

class ReadTask(BaseModel):
    id: int
    name: str
    priority_id: int
    priority_name: str | None = None
    project_id: int
    project_name: str
    created_by: int
    creator: UserRead
    weight: int | None
    description: str
    is_completed: bool
    without_time: bool
    start_at: datetime
    deadline_at: datetime
    members: list[TaskMemberRead]

    model_config = {"from_attributes": True}

class AllTasksResponse(BaseModel):
    items: List[ReadTask]
    next_cursor: Optional[int] = None

    model_config = {"from_attributes": True}

class UpdateTask(BaseModel):
    name: str | None = None
    description: str | None = None
    priority_id: int | None = None
    start_at: datetime | None = None
    deadline_at: datetime | None = None

    @field_validator("deadline_at")
    def deadline_after_start(cls, v, info):
        start = info.data.get("start_at")
        if start and v and v < start:
            raise ValueError("deadline_at must be after start_at")
        return v

class AddUserToTask(BaseModel):
    user_emails: list[EmailStr]
    task_id: int