from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import models
from app.models.models import Tasks, UsersTasks
from app.schemas.task_schema import ReadTask

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

    return res.scalar_one()

async def get_all_user_tasks_from_project_repository(
        db: AsyncSession,
        user_id: int,
        project_id: int,
        cursor: int = 0,
        limit: int = 5
) -> List[Tasks]:
    stmt = (
        select(Tasks)
        .join(Tasks.task_users)
        .where(
            Tasks.project_id == project_id,
            UsersTasks.user_id == user_id,
            Tasks.id > cursor  # курсор
        )
        .order_by(Tasks.id.asc())
        .limit(limit)
        .options(
            selectinload(Tasks.task_users)
            .selectinload(UsersTasks.user),
            selectinload(Tasks.task_users)
            .selectinload(UsersTasks.role),
        )
    )

    result = await db.execute(stmt)
    return result.scalars().all()

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
        task: Tasks
) -> Tasks:
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task

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