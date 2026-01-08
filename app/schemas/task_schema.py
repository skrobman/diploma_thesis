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
    description: Optional[str] = None

    start_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None

    start_date: Optional[date] = None
    start_time: Optional[time] = None

    deadline_date: Optional[date] = None
    deadline_time: Optional[time] = None

    without_time: bool = False
    users: List[EmailStr] = []

    @model_validator(mode="after")
    def compute_datetimes(self):
        # ===== without_time =====
        if self.without_time:
            if not self.start_date:
                raise ValueError("start_date is required when without_time=true")

            if any([self.start_time, self.deadline_time, self.start_at, self.deadline_at]):
                raise ValueError(
                    "Time or datetime fields are not allowed when without_time=true"
                )

            # deadline_date опциональна, по умолчанию = start_date
            deadline_date = self.deadline_date or self.start_date

            self.start_at = datetime.combine(
                self.start_date,
                time.min,
                tzinfo=timezone.utc
            )
            self.deadline_at = datetime.combine(
                deadline_date,
                time.max,
                tzinfo=timezone.utc
            )

        # ===== without_time=False =====
        else:
            # 🔹 Вариант 1: переданы datetime напрямую
            if self.start_at or self.deadline_at:
                if not (self.start_at and self.deadline_at):
                    raise ValueError("Both start_at and deadline_at must be provided")
            # 🔹 Вариант 2: переданы date/time
            else:
                if not self.start_date:
                    raise ValueError("start_date must be provided")

                start_time = self.start_time or time.min
                deadline_date = self.deadline_date or self.start_date
                deadline_time = self.deadline_time or time.max

                self.start_at = datetime.combine(
                    self.start_date,
                    start_time,
                    tzinfo=timezone.utc
                )
                self.deadline_at = datetime.combine(
                    deadline_date,
                    deadline_time,
                    tzinfo=timezone.utc
                )

        # ===== Проверка после расчёта =====
        if self.start_at >= self.deadline_at:
            raise ValueError("deadline_at must be after start_at")

        return self

class TaskMemberRead(BaseModel):
    role: str
    users: UserRead

    model_config = {"from_attributes": True}

class CalendarTasksRead(BaseModel):
    project_id: int
    task_id: int
    name: str
    description: str | None = None
    priority_id: int
    start_at: datetime
    deadline_at: datetime
    is_completed: bool
    is_overdue: bool = False

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_is_overdue(self):
        self.is_overdue = (
            not self.is_completed
            and self.deadline_at < datetime.now(timezone.utc)
        )
        return self

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
    without_time: bool | None = None

    @field_validator("deadline_at")
    def deadline_after_start(cls, v, info):
        start = info.data.get("start_at")
        if start and v and v < start:
            raise ValueError("deadline_at must be after start_at")
        return v

class AddUserToTask(BaseModel):
    user_emails: list[EmailStr]
    task_id: int

class RemoveUserFromTask(BaseModel):
    task_id: int
    user_emails: list[EmailStr]

class TaskArchive(BaseModel):
    task_id: int
    archive: bool