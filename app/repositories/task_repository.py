from datetime import date, timedelta, datetime, time, timezone
from typing import List, Optional, Dict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import models
from app.models.models import Tasks, UsersTasks, PriorityLevels
from app.schemas.task_schema import CreateTask, CalendarTasksRead
from app.utils.enums.enum_utils import TaskPeriod

async def get_all_priorities(
        db: AsyncSession
):
    result = await db.execute(
        select(PriorityLevels)
    )

    return result.scalars().all()

async def get_task_by_id_repository(db: AsyncSession, task_id: int) -> Tasks:
    res = await db.execute(
        select(Tasks)
        .where(Tasks.id == task_id)
        .options(
            selectinload(Tasks.task_users)
            .selectinload(UsersTasks.user),
            selectinload(Tasks.task_users)
            .selectinload(UsersTasks.role),
        )
    )

    return res.scalar_one_or_none()

async def get_all_user_tasks_for_calendar(
        db: AsyncSession,
        user_id: int,
        year: int,
        month: int,
):
    start_of_month = datetime(year, month, 1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

    stmt = (
        select(
            Tasks.project_id,
            Tasks.id.label("task_id"),
            Tasks.name,
            Tasks.description,
            Tasks.priority_id,
            Tasks.start_at,
            Tasks.deadline_at,
            Tasks.is_completed
        )
        .join(UsersTasks, Tasks.id == UsersTasks.task_id)
        .where(
            UsersTasks.user_id == user_id,
            Tasks.start_at <= end_of_month,
            Tasks.deadline_at >= start_of_month,
        )
        .order_by(Tasks.start_at)
    )

    result = await db.execute(stmt)
    tasks_from_db = result.all()

    return [CalendarTasksRead.model_validate(dict(row._mapping)) for row in tasks_from_db]


async def get_all_user_tasks_from_project_repository(
    db: AsyncSession,
    user_id: int,
    project_id: int,
    cursor: int = 0,
    limit: int = 5,
    priority_id: int | None = None,
    period: TaskPeriod | None = None,
) -> list[Tasks]:

    stmt = (
        select(Tasks)
        .join(UsersTasks, Tasks.id == UsersTasks.task_id)
        .where(
            Tasks.project_id == project_id,
            UsersTasks.user_id == user_id,
            Tasks.id > cursor
        )
    )

    filters = []

    if priority_id is not None:
        filters.append(Tasks.priority_id == priority_id)

    if period is not None:
        today = date.today()
        now = datetime.now()

        if period == TaskPeriod.today:
            start = datetime.combine(today, time.min)
            end = datetime.combine(today, time.max)
            filters.append(
                and_(
                    Tasks.start_at <= end,
                    Tasks.deadline_at >= start,
                    Tasks.is_completed == False,
                )
            )

        elif period == TaskPeriod.week:
            start_week = today - timedelta(days=today.weekday())
            end_week = start_week + timedelta(days=6)
            start = datetime.combine(start_week, time.min)
            end = datetime.combine(end_week, time.max)
            filters.append(
                and_(
                    Tasks.start_at <= end,
                    Tasks.deadline_at >= start,
                    Tasks.is_completed == False,
                )
            )

        elif period == TaskPeriod.overdue:
            filters.append(
                and_(
                    Tasks.deadline_at < now,
                    Tasks.is_completed == False,
                )
            )
        elif period == TaskPeriod.completed:
            filters.append(
                Tasks.is_completed == True
            )
        elif period == TaskPeriod.upcoming:
            filters.append(
                and_(
                    Tasks.start_at > now,
                    Tasks.is_completed == False,
                )
            )

        # filters.append(
        #     and_(
        #         Tasks.start_at <= end,
        #         Tasks.deadline_at >= start
        #     )
        # )

    stmt = stmt.where(*filters)

    stmt = (
        stmt
        .order_by(Tasks.id.asc())
        .limit(limit)
        .options(
            selectinload(Tasks.creator),
            selectinload(Tasks.task_users)
                .selectinload(UsersTasks.user),
            selectinload(Tasks.task_users)
                .selectinload(UsersTasks.role),
        )
    )

    result = await db.execute(stmt)
    return result.scalars().unique().all()

async def is_user_task_member(db: AsyncSession, task_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(UsersTasks)
        .where(
            UsersTasks.task_id == task_id,
            UsersTasks.user_id == user_id
        )
    )
    return result.scalar_one_or_none() is not None

async def create_task_repository(
    db: AsyncSession,
    task_data: CreateTask,
    creator_id: int,
    members_with_roles: Dict[int, int],
) -> Tasks:
    try:
        task_payload = task_data.model_dump(
            exclude={
                "users",
                "start_date",
                "start_time",
                "deadline_date",
                "deadline_time",
            }
        )

        new_task = Tasks(**task_payload)
        new_task.created_by = creator_id

        db.add(new_task)
        await db.flush()

        if members_with_roles:
            db.add_all(
                [
                    UsersTasks(
                        task_id=new_task.id,
                        user_id=user_id,
                        role_id=role_id,
                    )
                    for user_id, role_id in members_with_roles.items()
                ]
            )

        await db.commit()

        stmt = (
            select(Tasks)
            .where(Tasks.id == new_task.id)
            .options(
                selectinload(Tasks.creator),
                selectinload(Tasks.task_users)
                    .selectinload(UsersTasks.user),
                selectinload(Tasks.task_users)
                    .selectinload(UsersTasks.role),
            )
        )

        result = await db.execute(stmt)
        return result.scalar_one()

    except Exception:
        await db.rollback()
        raise


async def get_task_priority(
        db: AsyncSession,
        priority_id: int
):
    result = await db.execute(
        select(models.ProjectPurposes).where(
            models.ProjectPurposes.id == priority_id
        )
    )
    return result.scalars().first()

async def get_task_member_by_id(
        db: AsyncSession,
        task_id: int,
        user_id: int
):
    result = await db.execute(
        select(UsersTasks).where(
            UsersTasks.task_id == task_id,
            UsersTasks.user_id == user_id
        )
    )

    return result.scalars().first()