from typing import List, Optional, Dict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models import models
from app.models.models import Tasks, UsersTasks
from app.schemas.task_schema import ReadTask, CreateTask

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
        task_data: CreateTask,
        creator_id: int,
        members_with_roles: Dict[int, int]
) -> Tasks:
    try:
        # 1. Создаем и сохраняем задачу (как было)
        task_payload = task_data.model_dump(exclude={'users'})
        new_task = Tasks(**task_payload)
        new_task.created_by = creator_id

        db.add(new_task)
        await db.flush()

        # 2. Добавляем участников
        if members_with_roles:
            participants_to_add = []
            for uid, role_id in members_with_roles.items():
                participants_to_add.append(
                    UsersTasks(
                        task_id=new_task.id,
                        user_id=uid,
                        role_id=role_id
                    )
                )
            db.add_all(participants_to_add)

        await db.commit()

        # --- ВОТ ЭТОГО НЕ ХВАТАЛО ---
        # 3. Делаем выборку полной задачи с подгрузкой связей

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
        full_task = result.scalar_one()

        return full_task

    except Exception as e:
        await db.rollback()
        raise e

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